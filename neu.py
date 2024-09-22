from dataclasses import field

import cv2 as cv
import numpy as np
import time, datetime

from serial import Serial

import config as C
from config import ErrCode
from ThreadingCam import ThreadCap
from py_tic_tac_toe.game import best_move, decide_win, anti_cheat
from transmission import ser, ByteArray


def find_field(frame) -> np.array:
    frame = cv.GaussianBlur(frame, (5, 5), 0)
    mask = cv.inRange(frame, np.array([200, 200, 0]), np.array([255, 255, 200]))
    mask = cv.dilate(mask, None, iterations=2)
    mask = cv.erode(mask, None, iterations=2)
    # cv.imshow("mask", mask)
    cnts, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    if len(cnts) == 0:
        return None
    cnts = sorted(cnts, key=cv.contourArea, reverse=True)
    (x, y), (w, h), angle = cv.minAreaRect(cnts[0])
    if w < 100 or h < 100:
        return None
    centers = []
    # print(f"Angle: {angle}")
    angle = angle / 180 * np.pi if angle < 45 else (angle - 90) / 180 * np.pi
    mat = np.array([[np.cos(angle), -np.sin(angle)],
                    [np.sin(angle), np.cos(angle)]])
    ctr = np.array([x, y])
    for j in range(3):
        for i in range(3):
            point = np.array([x - w / 2 + (1 + 2 * i) * w / 6, y - h / 2 + (1 + 2 * j) * h / 6])
            point = np.dot(mat, point - ctr) + ctr
            centers.append(point)
    centers = np.array(centers, dtype=np.int32)
    # a vertical line
    # cv.line(frame, (int(x - w / 2), int(y - h / 2)), (int(x - w / 2), int(y + h / 2)), (0, 255, 0), 2)
    # cv.imshow("Find Field", frame)
    return centers


def read_board(frame, me) -> list | None:
    field = find_field(frame)
    board = [[" " for i in range(3)] for j in range(3)]
    if field is None:
        return None
    if me == 4:
        ego = "O"
        tu = "X"
    elif me == 5:
        ego = "X"
        tu = "O"
    else:
        return None
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    # cv.imshow("gray", gray)
    for idx, (cx, cy) in enumerate(field):
        cv.putText(frame, str(idx), (cx, cy), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
        cv.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
        brightness = np.mean(gray[cy - 10:cy + 10, cx - 10:cx + 10])
        if brightness < 150:
            board[idx // 3][idx % 3] = ego
        elif brightness > 240:
            board[idx // 3][idx % 3] = tu
    # cv.imshow("Read Board", frame)
    return board


def show_board(board) -> None:
    if board is None:
        return
    for row in board:
        print(" ".join(row))
    print()


def recv_cmd() -> int:
    if ser is None:
        return -1
    ret = 0
    if ser.in_waiting:
        bt = ser.read(1)
        print(f"Received {bt}")
        if bt == b'\xff':
            if ser.in_waiting:
                bt = ser.read(1)
                print(f"Received {bt}")
                if bt == b'\xb1':
                    ret = 4
                elif bt == b'\xc1':
                    ret = 5
                elif bt == b'\xa1':
                    if ser.in_waiting:
                        bt = ser.read(1)
                        print(f"Received {bt}")
                        if bt == b'\xa2':
                            ret = 2  # reset
                        else:
                            ret = 1  # unreset
                if ser.in_waiting:
                    bt = ser.read(1)
                    print(f"Received {bt}")
                    if bt != b'\xfe':
                        ret = 0
    return ret


def send_cmd(move) -> None:
    if move is None:
        return
    sent = [0xff, 0xa1]
    sent.append(move[0] * 3 + move[1] + 1)
    sent.append(0xfe)
    sent = ByteArray(sent)
    ser.write(sent)
    print(f"Sent {sent}")


def report_cheat(old_pos, new_pos) -> None:
    if ser is None:
        return
    sent = [0xff]
    sent.append(old_pos + 1)
    sent.append(new_pos + 1)
    sent.append(0xfe)
    sent = ByteArray(sent)
    ser.write(sent)
    print(f"Sent {sent}")


def main() -> None:
    if C.threading_cam:
        cap = ThreadCap(camera_index=C.cam_id, width=640, height=480, fps=120)
    else:
        cap = cv.VideoCapture(C.cam_id)
        cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter.fourcc(*"MJPG"))
        cap.set(cv.CAP_PROP_FPS, 120)
    if cap is None or not cap.isOpened():
        print("Fatal: Camera not opened")
        return ErrCode.CAM_NO_OPENED

    global ser
    try:
        ser = Serial(C.serial_port, C.serial_baud)
    except Exception as e:
        print(f"Fatal: Serial not opened: {e}")
        ser = None
        return ErrCode.SER_NOT_OPENED

    ret_code = 0
    err_times = 0

    ques = 0
    reset = False
    last_board = None
    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("Fatal: No frame got")
                if C.threading_cam:
                    continue
                else:
                    ret_code = ErrCode.NO_FRAME_GOT
                    break
            cmd = recv_cmd()
            if cmd == 2:
                reset = True
            elif cmd == 4 or cmd == 5:
                ques = cmd
            else:
                reset = False
            # print(f"Ques: {ques}, Reset: {reset}")
            board = read_board(frame, ques) if reset else None
            # board = read_board(frame, 4)
            show_board(board)
            if board:
                if last_board:
                    print("Last board:")
                    show_board(last_board)
                    cheat, old_pos, new_pos = anti_cheat(last_board, board)
                    if cheat:
                        print(f"Cheat: {old_pos + 1} -> {new_pos + 1}")
                        report_cheat(new_pos, old_pos)
                        continue
                move = best_move(board)
                print(move)
                send_cmd(move)
                board[move[0]][move[1]] = "O"
                last_board = board
            cv.imshow("frame", frame)
            key = cv.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                ques = 0
                reset = False
                board = None
                last_board = None
                ret_code = 0
                err_times = 0
        except Exception as e:
            print(f"Error: {e}")
            err_times += 1
            if err_times > 10:
                ret_code = -1
                break
    return ret_code


if __name__ == '__main__':
    exit(main())
