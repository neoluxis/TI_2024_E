import cv2 as cv
import numpy as np
import time, datetime

from serial import Serial

import Final.config as C
from Final.config import ErrCode
from ThreadingCam import ThreadCap
from py_tic_tac_toe.game import best_move, decide_win, anti_cheat
from detection import find_field, find_pieces, read_board
from transmission import ser, send_field, send_pieces, notify_winner, notify_cheat


def main():
    if C.threading_cam:
        cap = ThreadCap(camera_index=0, width=640, height=480, fps=120)
    else:
        cap = cv.VideoCapture(0)
        cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter.fourcc(*"MJPG"))
        cap.set(cv.CAP_PROP_FPS, 120)
    if cap is None or not cap.isOpened():
        print("Fatal: Camera not opened")
        return ErrCode.CAM_NO_OPENED
    global ser
    ser = Serial(C.serial_port, C.serial_baud)
    # ser = None
    failed_to_decide = False
    if C.debug:
        fc = 0  # frame count
        t0 = datetime.datetime.now()
        last_pole = [-1, -1]
        last_board = None
        while True:
            ret, frame = cap.read()
            fm = frame.copy() if not frame is None else None
            if not ret:
                print("Fatal: No frame got")
                if C.threading_cam:
                    continue
                else:
                    return ErrCode.NO_FRAME_GOT
            fc += 1
            centers, pole = find_field(frame)
            send_field(centers)
            pieces = find_pieces(frame, pole[0], pole[1]) if not pole[0] == -1 else None
            # if pole[0] == -1:
            #      pole = last_pole
            # pieces = find_pieces(frame, pole[0], pole[1]) if not pole[0] == -1 else None
            send_pieces(pieces)

            if ser.in_waiting > 0 or failed_to_decide:
                if not failed_to_decide:
                    cmd = ser.read_all()
                print("Cmd: ", cmd)
                if cmd == b"4":
                    board = read_board(fm, 4)
                elif cmd == b"5":
                    board = read_board(fm, 5)
                else:
                    
                    continue
                print("Board:\n", board)
                print("Last Board: \n", last_board)
                if not last_board is None:
                    ret, old_pos, new_pos = anti_cheat(last_board, board)
                    if ret:
                        print("Anti-cheat detected: ", old_pos, "->", new_pos)
                        notify_cheat(old_pos, new_pos)
                        continue
                last_board = board
                winner = decide_win(board)
                # print("Winner 1: ", winner)
                if winner == -1:
                    notify_winner("human")  # 人类获胜
                elif winner == 3:
                    notify_winner("draw")  # 平局
                elif winner == 0:  # 不确定结果
                    bm = best_move(board)
                    print(bm)
                    if bm is None:
                        failed_to_decide = True
                        continue
                    board[bm[0]][bm[1]] = "O"
                    bm1 = bm[0] * 3 + bm[1]
                    ba = ByteArray([0xFF, 0x03, bm1, 0xFE])
                    ser.write(ba)
                    print(ba)
                    failed_to_decide = False
                    winner = decide_win(board)  # 再次检查是否结束
                    if winner == 1:
                        notify_winner("computer")
                    elif winner == 3:
                        notify_winner("draw")
                    # board[bm[0]][bm[1]] = " "

            cv.imshow("Frame", frame)

            key = cv.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            t1 = datetime.datetime.now()
            if (t1 - t0).total_seconds() > 1:
                print(f"FPS: {fc / (t1 - t0).total_seconds():.2f}")
                fc = 0
                t0 = t1
            last_pole = pole
        cap.release()
        return 0
    else:
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Fatal: No frame got")
                    return ErrCode.NO_FRAME_GOT
                find_field(frame)
        except KeyboardInterrupt:
            cap.release()
            return 0


if __name__ == "__main__":
    exit(main())
