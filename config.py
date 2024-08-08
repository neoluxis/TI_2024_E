debug = True

# 通讯参数
serial_port = "/dev/ttyAMA2"
serial_baud = 115200

# 是否使用多线程读取摄像机
threading_cam = True

# 主程序返回值
class ErrCode:
    CAM_NO_OPENED = 229
    NO_FRAME_GOT = 230

