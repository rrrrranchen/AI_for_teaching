import os

# 定义静态文件夹路径
static_folder = 'backend/app/static/uploads/'
file_path = os.path.join(static_folder, 'opensuse.png')

# 检查文件是否存在
if os.path.exists(file_path):
    print("File exists at:", file_path)
else:
    print("File does not exist.")