import os
from werkzeug.utils import secure_filename

# 定义 uploads 目录路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(project_root, 'static', 'uploads')

# 确保 uploads 目录存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file(file):
    """上传文件并返回文件路径"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # 返回相对于静态目录的路径
        relative_path = os.path.join('static', 'uploads', filename)
        return relative_path
    else:
        raise ValueError("不支持的文件类型")