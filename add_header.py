import os
import datetime

def add_file_header(file_path, author, description, version="1.0", copyright_info=""):
    # 获取当前日期
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在。")
        return

    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 文件头部信息
    header = f"""
\"\"\"
filename: {os.path.basename(file_path)}
author: {author}
created: {current_date}
last modified: {current_date}
descrip: {description}
version: {version}
copyright: {copyright_info}
\"\"\"

"""
    # 写入文件头部信息
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(header + content)

    print(f"Added to {file_path}")

# 示例使用
file_path = 'Final/ThreadingCam.py'
author = 'Neolux Lee'
description = ''
version = '1.0'
copyright_info = '© 2024 N.K.F.Lee'

add_file_header(file_path, author, description, version, copyright_info)
