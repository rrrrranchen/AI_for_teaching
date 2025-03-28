import os
from typing import Set, Optional
from flask import current_app

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

def allowed_file(
    filename: str, 
    extensions: Optional[Set[str]] = None,
    check_mime: bool = True
) -> bool:
    """
    验证文件扩展名和MIME类型是否允许
    
    Args:
        filename: 文件名
        extensions: 允许的扩展名集合（默认使用配置中的ALLOWED_EXTENSIONS）
        check_mime: 是否验证实际文件的MIME类型
    
    Returns:
        bool: 是否允许上传
    """
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    allowed_ext = extensions or current_app.config.get('ALLOWED_EXTENSIONS', set())
    
    # 扩展名检查
    if ext not in allowed_ext:
        return False
    
    # 可选MIME类型验证
    if check_mime and hasattr(current_app, 'config'):
        from magic import Magic
        mime = Magic(mime=True)
        file_mime = mime.from_file(filename)
        expected_mime = MIME_TYPE_MAP.get(ext)
        
        if expected_mime and file_mime != expected_mime:
            current_app.logger.warning(
                f"MIME类型不匹配: 文件{file_mime} != 预期{expected_mime}"
            )
            return False
    
    return True


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