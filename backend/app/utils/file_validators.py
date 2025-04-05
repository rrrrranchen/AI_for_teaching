import os
from typing import Set, Optional
from flask import current_app
from filetype import guess
# 支持的MIME类型映射
MIME_TYPE_MAP = {
    'pdf': 'application/pdf',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'jpg': 'image/jpeg',
    'png': 'image/png',
    'mp4': 'video/mp4',
    'mp3': 'audio/mpeg'
}

def allowed_file(filename):
    """使用 filetype 替代 python-magic"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'pdf', 'docx','pptx','ppt'}
    
    # 基础扩展名检查
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    
    # 验证真实文件类型（上传后检查）
    def validate_real_type(file_path):
        kind = guess(file_path)
        if kind and kind.extension not in ALLOWED_EXTENSIONS:
            os.remove(file_path)  # 删除不符合类型的文件
            return False
        return True
    
    return ext in ALLOWED_EXTENSIONS, validate_real_type

def validate_file_signature(filepath: str) -> bool:
    """
    通过文件头验证文件真实类型
    
    Args:
        filepath: 文件路径
    
    Returns:
        bool: 文件签名是否有效
    """
    # 文件类型签名映射（魔数）
    SIGNATURES = {
        'pdf': b'%PDF',
        'jpg': b'\xFF\xD8\xFF',
        'png': b'\x89PNG',
        'mp4': b'\x00\x00\x00\x18ftypmp42',
        'zip': b'PK\x03\x04'  # 也适用于docx/pptx
    }
    
    try:
        with open(filepath, 'rb') as f:
            header = f.read(32)  # 读取前32字节
            
        ext = os.path.splitext(filepath)[1][1:].lower()
        expected_sig = SIGNATURES.get(ext)
        
        if expected_sig:
            return header.startswith(expected_sig)
        return True
    except:
        return False