import cv2 as cv
import numpy as np
import time, datetime

import config as C
from config import ErrCode


def is_square(contour):
    """判断是否为方格

    Args:
        contour (_type_): 一个轮廓

    Returns:
        _type_: 方格中心坐标，若不是方格则返回 (-1, -1)
    """
    perimeter = cv.arcLength(contour, True)
    approx = cv.approxPolyDP(contour, 0.04 * perimeter, True)
    (x, y), (w, h), angle = cv.minAreaRect(contour)
    if len(approx) == 4 and 0.9 < cv.contourArea(contour) / (w * h) < 1.1:
        M = cv.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return cx, cy
    return -1, -1


def vector_angle(vec1, vec2):
    """Calculate the angle between two vectors. (0 < angle < 180)

    Args:
        vec1 (_type_): _description_
        vec2 (_type_): _description_
    """
    angle = np.arccos(
        np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    )
    # if np.cross(vec1, vec2) < 0:
    #     angle = -angle
    return np.degrees(angle)


def arrange_block(centers, angle):
    """重新排列单元格中心点的顺序
    使之按照题目要求，从左上角开始，行列排序
    OpenCV识别结果在正直状态下默认顺序即为正确顺序
    旋转 +-45° 时，需要重新排列，对此直接分类，减少计算量

    Args:
        centers (_type_): 坐标列表

    Returns:
        _type_: 排序好的坐标列表
    """
    if not len(centers) == 9:
        return []
    centers = np.array(centers)
    vec01 = centers[1] - centers[0]
    vec02 = centers[2] - centers[0]
    angle201 = vector_angle(vec02, vec01)
    # print(f"Angle201: {angle201}")
    if angle201 < 10:
        if 60 < angle < 90:
            centers = [centers[x] for x in [2, 1, 0, 5, 4, 3, 8, 7, 6]]
            return centers
        elif angle < 30 or angle == 90:
            return centers
    elif 85 < angle201 < 95:
        if angle > 45:
            centers = [centers[x] for x in [3, 1, 0, 6, 4, 2, 8, 7, 5]]
        else:
            centers = [centers[x] for x in [0, 1, 3, 2, 4, 6, 5, 7, 8]]
    return centers


def find_field(frame):
    """查找棋盘

    Args:
        frame (cv.Mat): 图片一帧

    Returns:
        _type_: 排序后的中心坐标列表，左右极限的坐标
    """
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray, (5, 5), 0)
    if np.mean(gray) < 10:
        return [], [-1, -1]
    # cv.imshow("Grayscale", gray)
    _, thres = cv.threshold(gray, 0, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)
    thres = cv.erode(thres, None, iterations=2)
    # cv.imshow("Threshold", thres)
    blocks, _ = cv.findContours(thres, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    centers = []
    sample = None
    for idx, block in enumerate(blocks):
        area = cv.contourArea(block)
        if area < 1000:
            continue
        cx, cy = is_square(block)
        if cx == -1:
            continue
        centers.append([cx, cy])
        sample = block
        if C.debug:
            cv.drawContours(frame, [block], -1, (0, 255, 0), 2)
            cv.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            # cv.imshow("Find Field", frame)
    try:
        (x, y), (w, h), angle = cv.minAreaRect(sample)
    except:
        return [], [-1, -1]
    if not len(centers) == 9:
        return [], [-1, -1]
    else:
        pole = [
            int(min(centers, key=lambda x: x[0])[0] - w // 2),
            int(max(centers, key=lambda x: x[0])[0] + w // 2),
        ]
        # print("Pole:", pole)
    # print(f"Angle: {angle}")

    centers = arrange_block(centers, angle)

    for idx, (cx, cy) in enumerate(centers):
        cv.putText(
            frame, str(idx), (cx, cy), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2
        )
    # cv.imshow("Find Field", frame)

    return centers, pole


def is_circle(contour):
    """判断是否为圆，是否是棋子

    Args:
        contour (_type_): 一个轮廓

    Returns:
        _type_: 圆心坐标，若不是圆则返回 (-1, -1)
    """
    # outer edge
    perimeter = cv.arcLength(contour, True)
    approx = cv.approxPolyDP(contour, 0.03 * perimeter, True)
    (x, y), r = cv.minEnclosingCircle(contour)
    if len(approx) >= 6 and 0.7 < cv.contourArea(contour) / (np.pi * r**2) < 1.3:
        (x, y), r = cv.minEnclosingCircle(contour)
        return int(x), int(y)
    return -1, -1


def find_pieces(frame, left=180, right=450):
    """截取棋盘两侧ROI，查找棋子

    Args:
        frame (_type_): 图片一帧
        left (int, optional): 左侧截取的边界. Defaults to 180.
        right (int, optional): 右侧……. Defaults to 450.

    Returns:
        _type_: 棋子坐标字典，包含黑棋和白棋的坐标列表
    """
    if left < 10 or right > 630:  # 如果ROI不靠谱就直接别算了
        return {"black": [], "white": []}
    rightwing = frame[:, :left, :]  # white
    leftwing = frame[:, right:, :]  # black
    pieces = {"black": [], "white": []}
    gray = cv.cvtColor(leftwing, cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray, (5, 5), 0)
    _, thres = cv.threshold(gray, 0, 255, cv.THRESH_BINARY_INV | cv.THRESH_OTSU)
    thres = cv.erode(thres, None, iterations=2)
    cnts, _ = cv.findContours(thres, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    for idx, cnt in enumerate(cnts):
        area = cv.contourArea(cnt)
        if area < 1000 or not is_circle(cnt):
            continue
        cx, cy = is_circle(cnt)
        if cx == -1:
            continue
        pieces["black"].append([cx, cy])
        if C.debug:
            cv.drawContours(leftwing, [cnt], -1, (0, 255, 0), 2)
            cv.circle(leftwing, (cx, cy), 5, (0, 0, 255), -1)
            # cv.imshow("left", leftwing)
    # cv.imshow("left thres", thres)

    gray = cv.cvtColor(rightwing, cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray, (5, 5), 0)
    # cv.imshow("Gray", gray)
    _, thres = cv.threshold(gray, 0, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)
    thres = cv.erode(thres, None, iterations=2)
    cnts, _ = cv.findContours(thres, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    for idx, cnt in enumerate(cnts):
        area = cv.contourArea(cnt)
        if area < 1000 or not is_circle(cnt):
            continue
        cx, cy = is_circle(cnt)
        if cx == -1:
            continue
        pieces["white"].append([cx, cy])
        if C.debug:
            cv.drawContours(rightwing, [cnt], -1, (0, 255, 0), 2)
            cv.circle(rightwing, (cx, cy), 5, (0, 0, 255), -1)
            # cv.imshow("right", rightwing)
    # cv.imshow("right thres", thres)
    pieces["black"] = sorted(pieces["black"], key=lambda x: x[1])
    pieces["white"] = sorted(pieces["white"], key=lambda x: x[1])
    pieces["black"] = [
        [pieces["black"][x][0] + right, pieces["black"][x][1]]
        for x in range(len(pieces["black"]))
    ]
    if C.debug:
        for idx, piece in enumerate(pieces["black"]):
            cv.putText(
                leftwing,
                str(idx),
                (piece[0], piece[1]),
                cv.FONT_HERSHEY_SIMPLEX,
                1,
                (128, 128, 255),
                2,
            )
        for idx, piece in enumerate(pieces["white"]):
            cv.putText(
                rightwing,
                str(idx),
                (piece[0], piece[1]),
                cv.FONT_HERSHEY_SIMPLEX,
                1,
                (128, 128, 255),
                2,
            )
        # cv.imshow("right", rightwing)
    return pieces


blocks_center = []


def read_board(frame, me):
    """根据棋盘坐标读取棋盘状态

    Args:
        frame (_type_): 图片
        me (_type_): 我的棋子颜色（表现为任务编号）

    Returns:
        _type_: 棋盘状态数组
    """
    global blocks_center
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    cv.imshow("Gray", gray)
    board = [[" " for i in range(3)] for j in range(3)]
    if me == 4:
        ego = "X"
        tu = "O"
    elif me == 5:
        ego = "O"
        tu = "X"
    for idx, block in enumerate(blocks_center):
        color = gray[block[1], block[0]]
        # print("Color: ", color)
        if color > 210:
            board[idx // 3][idx % 3] = ego
        elif color < 100:
            board[idx // 3][idx % 3] = tu
    return board
