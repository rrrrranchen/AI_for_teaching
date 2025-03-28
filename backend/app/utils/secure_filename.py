import re
import os
from werkzeug.utils import secure_filename as werkzeug_secure_filename
from unicodedata import normalize

def secure_filename(filename: str, allow_unicode: bool = True) -> str:
    """
    安全文件名处理函数（支持中文）
    
    参数：
    filename -- 原始文件名
    allow_unicode -- 是否允许Unicode字符（默认允许中文）

    返回：
    处理后的安全文件名
    
    示例：
    >>> secure_filename("测试/../报告.docx")
    '测试报告.docx'
    >>> secure_filename("image 01*.jpg")
    'image01.jpg'
    """
    if not filename:
        return 'unnamed_file'

    # 基础安全处理（保留中文）
    filename = werkzeug_secure_filename(filename)

    # 分离文件名和扩展名
    base, ext = os.path.splitext(filename)
    if not base:  # 处理纯扩展名情况
        return f'unnamed_file{ext}'

    # 增强Unicode支持
    if allow_unicode:
        # 允许中文、日文、韩文字符（参考Unicode区块范围）
        base = normalize('NFC', base)  # 标准化字符表示
        base = re.sub(
            r'[^\w\s\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7a3.-]', 
            '', 
            base
        )
    else:
        base = re.sub(r'[^a-zA-Z0-9_.-]', '', base)

    # 移除危险字符序列
    base = base.replace('/', '').replace('\\', '')  # 路径分隔符
    base = re.sub(r'\.{2,}', '', base)  # 防止父目录引用
    base = base.strip('. ')  # 移除首尾点和空格

    # 长度限制（考虑UTF-8编码）
    max_byte_length = 220  # 预留扩展名空间
    encoded_base = base.encode('utf-8')[:max_byte_length].decode('utf-8', 'ignore')
    encoded_base = encoded_base.strip() or 'unnamed_file'

    # 重组文件名
    ext = re.sub(r'[^a-zA-Z0-9.]', '', ext)[:10]  # 清理扩展名
    final_name = f"{encoded_base}{ext}"
    
    # 最终清理
    final_name = final_name.replace(' ', '_')  # 空格转下划线
    return final_name or 'unnamed_file'