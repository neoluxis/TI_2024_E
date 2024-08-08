"""
filename: minimaxd.py
author: Neolux Lee
created: 2024-07-29
last modified: 2024-07-29
descrip: 
version: 1.0
copyright: © 2024 N.K.F.Lee
"""

import math
import random


def print_board(board):
    for row in board:
        print(" | ".join(row))
        print("-" * 5)


def check_winner(board, player):
    # 检查行
    for row in board:
        if all([cell == player for cell in row]):
            return True
    # 检查列
    for col in range(3):
        if all([board[row][col] == player for row in range(3)]):
            return True
    # 检查对角线
    if all([board[i][i] == player for i in range(3)]):
        return True
    if all([board[i][2 - i] == player for i in range(3)]):
        return True
    return False


def decide_win(board):
    if check_winner(board, "X"):
        return -1
    elif check_winner(board, "O"):
        return 1
    elif not get_available_moves(board):
        return 3
    else:
        return 0


def get_available_moves(board):
    moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == " ":
                moves.append((i, j))
    return moves


def minimax(board, depth, is_maximizing):
    if check_winner(board, "X"):
        return -1
    elif check_winner(board, "O"):
        return 1
    elif not get_available_moves(board):
        return 0

    if is_maximizing:
        best_score = -math.inf
        for move in get_available_moves(board):
            board[move[0]][move[1]] = "O"
            score = minimax(board, depth + 1, False)
            board[move[0]][move[1]] = " "
            best_score = max(score, best_score)
        return best_score
    else:
        best_score = math.inf
        for move in get_available_moves(board):
            board[move[0]][move[1]] = "X"
            score = minimax(board, depth + 1, True)
            board[move[0]][move[1]] = " "
            best_score = min(score, best_score)
        return best_score


def alpha_beta(board, depth, alpha, beta, is_maximizing):
    if check_winner(board, "X"):
        return -1
    elif check_winner(board, "O"):
        return 1
    elif not get_available_moves(board):
        return 0

    if is_maximizing:
        best_score = -math.inf
        for move in get_available_moves(board):
            board[move[0]][move[1]] = "O"
            score = alpha_beta(board, depth + 1, alpha, beta, False)
            board[move[0]][move[1]] = " "
            best_score = max(score, best_score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return best_score
    else:
        best_score = math.inf
        for move in get_available_moves(board):
            board[move[0]][move[1]] = "X"
            score = alpha_beta(board, depth + 1, alpha, beta, True)
            board[move[0]][move[1]] = " "
            best_score = min(score, best_score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return best_score


def count_pieces(board):
    ci = 0
    for i in range(3):
        for j in range(3):
            if board[i][j] != " ":
                ci += 1
    return ci


def random_drop():
    space = [0, 1, 2, 3, 5, 6, 7, 8]
    choice = random.choice(space)
    return choice // 3, choice % 3


def best_move(board, method="minimax"):
    best_score = -math.inf
    move = None
    if board[1][1] == " ":
        return (1, 1)
    # elif count_pieces(board) < 2:
    #     return random_drop()
    for m in get_available_moves(board):
        board[m[0]][m[1]] = "O"
        score = (
            minimax(board, 0, False)
            if method == "minimax"
            else (
                alpha_beta(board, 0, -math.inf, math.inf, False)
                if method == "alpha-beta"
                else 0
            )
        )
        board[m[0]][m[1]] = " "
        if score > best_score:
            best_score = score
            move = m
    return move


def find_ego(board):
    positions = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == "O":
                positions.append((i, j))
    return positions


def anti_cheat(last_board, board):
    last_pieces = count_pieces(last_board)
    pieces = count_pieces(board)
    if pieces - last_pieces == 1:
        return False, 0, 0
    last_posis = find_ego(last_board)
    posis = find_ego(board)
    if len(last_posis) == 0 or len(posis) == 0:
        return False, 0, 0
    for posi in posis:
        if posi not in last_posis:
            new_pos = posi[0] * 3 + posi[1]
    for posi in last_posis:
        if posi not in posis:
            old_pos = posi[0] * 3 + posi[1]
    try:
        return True, old_pos, new_pos
    except:
        return False, 0, 0


def main():
    board = [[" " for _ in range(3)] for _ in range(3)]
    print("井字棋游戏开始！")
    print_board(board)

    while True:
        # 玩家移动
        row, col = map(int, input("请输入你的移动（行 列）：").split())
        if board[row][col] != " ":
            print("无效的移动，请重试。")
            continue
        board[row][col] = "X"

        if check_winner(board, "X"):
            print("你赢了！")
            break
        if not get_available_moves(board):
            print("平局！")
            break

        # 电脑移动
        move = best_move(board, "alpha-beta")
        board[move[0]][move[1]] = "O"
        print_board(board)

        if check_winner(board, "O"):
            print("你输了！")
            break
        if not get_available_moves(board):
            print("平局！")
            break


if __name__ == "__main__":
    # main()
    # board1 = [["X", "O", " "], [" ", "O", " "], [" ", " ", "X"]]
    # board2 = [["X", " ", "O"], [" ", "O", " "], [" ", " ", "X"]]
    # print_board(board1)
    # print()
    # print_board(board2)

    # ret, old_pos, new_pos = anti_cheat(board1, board2)
    # if ret:
    #     print(old_pos, "->", new_pos)
    board =  [[' ', ' ', ' '], [' ', 'X', ' '], [' ', ' ', ' ']]
    bm = best_move(board)
    print(bm)