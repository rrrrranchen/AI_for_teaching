import os
from werkzeug.utils import secure_filename
import time
import uuid
# 定义 uploads 目录路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER_PPTTEMPLATE=os.path.join(project_root,'static','template')
UPLOAD_FOLDER = os.path.join(project_root, 'static', 'uploads','avatar')
UPLOAD_FOLDER_FORUM=os.path.join(project_root, 'static', 'uploads','forum')
UPLOAD_FOLDER_COURSECLASS=os.path.join(project_root,'static','uploads','courseclass')
# 确保 uploads 目录存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXTENSIONS_PPT ={'ppt','pptx'}
def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file_ppt(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS_PPT

def upload_file_avatar(file):
    """上传文件并返回文件路径"""
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        random_string = uuid.uuid4().hex[:6]  # 生成6位随机字符串
        filename, ext = os.path.splitext(original_filename)
        unique_filename = f"{filename}_{timestamp}_{random_string}{ext}"  # 添加时间戳和随机字符串
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # 返回相对于静态目录的路径
        relative_path = os.path.join('static', 'uploads', 'avatar', unique_filename)
        return relative_path
    else:
        raise ValueError("不支持的文件类型")
    

def upload_file_forum(file):
    """上传文件并返回文件路径"""
    if file:
        original_filename = secure_filename(file.filename)
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        random_string = uuid.uuid4().hex[:6]  # 生成6位随机字符串
        filename, ext = os.path.splitext(original_filename)
        unique_filename = f"{filename}_{timestamp}_{random_string}{ext}"  # 添加时间戳和随机字符串
        file_path = os.path.join(UPLOAD_FOLDER_FORUM, unique_filename)
        file.save(file_path)
        
        # 返回相对于静态目录的路径
        relative_path = os.path.join('static', 'uploads', 'forum', unique_filename)
        return relative_path
    else:
        raise ValueError("不支持的文件类型")


def upload_file_courseclass(file):
    """上传文件并返回文件路径"""
    if file:
        original_filename = secure_filename(file.filename)
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        random_string = uuid.uuid4().hex[:6]  # 生成6位随机字符串
        filename, ext = os.path.splitext(original_filename)
        unique_filename = f"{filename}_{timestamp}_{random_string}{ext}"  # 添加时间戳和随机字符串
        file_path = os.path.join(UPLOAD_FOLDER_COURSECLASS, unique_filename)
        file.save(file_path)
        
        # 返回相对于静态目录的路径
        relative_path = os.path.join('static', 'uploads', 'courseclass', unique_filename)
        return relative_path
    else:
        raise ValueError("不支持的文件类型")

def upload_file_ppt_template(file):
    """上传文件并返回文件路径"""
    if file:
        original_filename = secure_filename(file.filename)
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        random_string = uuid.uuid4().hex[:6]  # 生成6位随机字符串
        filename, ext = os.path.splitext(original_filename)
        unique_filename = f"{filename}_{timestamp}_{random_string}{ext}"  # 添加时间戳和随机字符串
        file_path = os.path.join(UPLOAD_FOLDER_PPTTEMPLATE, unique_filename)
        file.save(file_path)
        
        # 返回相对于静态目录的路径
        relative_path = os.path.join('static', 'template', unique_filename)
        return relative_path
    else:
        raise ValueError("不支持的文件类型")