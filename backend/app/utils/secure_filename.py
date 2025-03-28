import re
import os
from unicodedata import normalize
from werkzeug.utils import secure_filename as werkzeug_secure_filename

def secure_filename(filename: str, allow_unicode: bool = False) -> str:
    """
    增强版安全文件名处理，基于Werkzeug的安全函数扩展
    
    Args:
        filename: 原始文件名
        allow_unicode: 是否允许Unicode字符
    
    Returns:
        安全处理后的文件名
    """
    # 基础安全处理
    filename = werkzeug_secure_filename(filename)
    
    # 额外处理：移除连续点和特殊字符
    filename = re.sub(r'(?i)[^a-z0-9_.-]', '', filename)
    
    # 处理Unicode字符（可选）
    if allow_unicode:
        filename = normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    
    # 移除路径分隔符（防御目录遍历）
    filename = filename.replace('/', '').replace('\\', '')
    
    # 截断过长的文件名（保留扩展名）
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        ext_length = len(ext)
        filename = f"{name[:max_length-ext_length-1]}{ext}"
    
    return filename or 'unnamed_file'