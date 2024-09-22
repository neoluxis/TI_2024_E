from serial import Serial

ser = None


class ByteArray(bytearray):
    def __init__(self, data):
        super().__init__(data)
        self.data = data

    def __str__(self):
        return f"[{', '.join([f'0x{byte:02X}' for byte in self.data])}]"


def send_field(vertices):
    global ser
    global blocks_center
    if not ser:
        return
    if not len(vertices) == 9:
        return
    blocks_center = vertices
    for idx, vertex in enumerate(vertices):
        sent = [0xFF, 0x02, idx]
        sent.append(vertex[0] >> 8)
        sent.append(vertex[0] & 0xFF)
        sent.append(vertex[1] >> 8)
        sent.append(vertex[1] & 0xFF)
        sent.append(0xFE)
        sent = ByteArray(sent)
        ser.write(sent)
        # print(f"Field: {sent}")
    print("Sent Field! ")


def send_pieces(pieces):
    global ser
    if not ser:
        return
    if not pieces:
        return
    # if len(pieces["black"]) == 0 and len(pieces["white"]) == 0:
    #     return
    for idx, black in enumerate(pieces["black"]):
        sent = [0xFF, 0x01, 0x01, idx]
        sent.append(black[0] >> 8)
        sent.append(black[0] & 0xFF)
        sent.append(black[1] >> 8)
        sent.append(black[1] & 0xFF)
        sent.append(0xFE)
        sent = ByteArray(sent)
        ser.write(sent)
        # print(f"White Piece: {sent}")
    for idx, white in enumerate(pieces["white"]):
        sent = [0xFF, 0x01, 0x02, idx]
        sent.append(white[0] >> 8)
        sent.append(white[0] & 0xFF)
        sent.append(white[1] >> 8)
        sent.append(white[1] & 0xFF)
        sent.append(0xFE)
        sent = ByteArray(sent)
        ser.write(sent)
        # print(f"Black Piece: {sent}")
    print("Sent Pieces! ")


def notify_winner(winner):
    global ser
    if not ser:
        return
    sent = [0xFF, 0x04, 0, 0xFE]
    match winner:
        case "unsure":
            sent[2] = 0
        case "computer":
            sent[2] = 1
        case "human":
            sent[2] = 2
        case "draw":
            sent[2] = 3
    sent = ByteArray(sent)
    ser.write(sent)
    print("Winner: ", winner)


def notify_cheat(old_pos, new_pos):
    global ser
    if not ser:
        return
    msg = ByteArray([0xFF, 0x05, old_pos, new_pos, 0xFE])  # 发送旧的序号和新的序号
    ser.write(msg)
    print("Cheat! ", msg)
