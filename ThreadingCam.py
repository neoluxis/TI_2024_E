"""
filename: ThreadingCam.py
author: Neolux Lee
created: 2024-08-09
last modified: 2024-08-09
descrip: 
version: 1.0
copyright: © 2024 N.K.F.Lee
"""

import cv2 as cv
import threading
import time
import numpy as np
from datetime import datetime


class Frame:
    def __init__(self, image, timestamp):
        self.image = image
        self.timestamp = timestamp


class ThreadCap:
    def __init__(self, camera_index=0, width=640, height=400, fps=240):
        self.cap = cv.VideoCapture(camera_index)
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter.fourcc(*"MJPG"))
        self.cap.set(cv.CAP_PROP_FPS, fps)

        self.frame = None
        self.last_frame = None
        self.lock = threading.Lock()
        self.stop_flag = False

        self.thread = threading.Thread(target=self._update_frame, daemon=True)
        self.thread.start()

    def _update_frame(self):
        while not self.stop_flag:
            ret, frame_gray = self.cap.read()
            if ret:
                # frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

                if not self.last_frame or not self._are_frames_similar(
                    frame_gray, self.last_frame.image
                ):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                    frame_with_timestamp = self._add_timestamp(frame_gray, timestamp)

                    with self.lock:
                        self.frame = Frame(frame_with_timestamp, timestamp)
                        self.last_frame = Frame(frame_gray, timestamp)

    def _compute_mse(self, imageA, imageB):
        """计算两张图片的均方误差"""
        err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
        err /= float(imageA.shape[0] * imageA.shape[1])
        return err

    def _are_frames_similar(self, frame1, frame2, threshold=10):
        """判断两张图片是否相似"""
        mse = self._compute_mse(frame1, frame2)
        return mse < threshold

    def _add_timestamp(self, frame, timestamp):
        """在图像上添加时间戳"""
        font = cv.FONT_HERSHEY_SIMPLEX
        # cv.putText(frame, timestamp, (10, 30), font, 1, (255), 2, cv.LINE_AA)
        return frame

    def read(self):
        with self.lock:
            frame_copy = self.frame.image.copy() if self.frame is not None else None
            timestamp = self.frame.timestamp if self.frame is not None else None
        return (timestamp, frame_copy)

    def isOpened(self):
        return self.cap.isOpened()

    def release(self):
        self.stop_flag = True
        self.thread.join()
        self.cap.release()


# 使用 ThreadCap 类
def main():
    cam = ThreadCap(camera_index=0, width=640, height=400)

    fourcc = cv.VideoWriter.fourcc(*"XVID")
    out = cv.VideoWriter("output.avi", fourcc, 30.0, (640, 400))

    try:
        while True:
            timestamp, frame = cam.read()
            if frame is not None:
                # 将灰度图像转换为 BGR 格式
                # frame_bgr = cv.cvtColor(frame, cv.COLOR_GRAY2BGR)
                cv.imshow("Camera Frame", frame)
                # out.write(frame_bgr)
                print(f"Timestamp: {timestamp}")
                if cv.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        out.release()
        cam.release()
        cv.destroyAllWindows()


if __name__ == "__main__":
    main()
