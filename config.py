debug = True

# 通讯参数
serial_port = "/dev/ttyUSB0"
serial_baud = 9600

# 是否使用多线程读取摄像机
threading_cam = False
cam_id = 2
# 主程序返回值
class ErrCode:
    CAM_NO_OPENED = 229
    NO_FRAME_GOT = 230
    SER_NOT_OPENED = 231

