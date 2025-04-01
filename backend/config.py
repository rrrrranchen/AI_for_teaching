import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    # 文件上传配置
    
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx', 'jpg', 'png', 'mp4', 'mp3','doc'}
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    
    # 预览图尺寸配置
    PREVIEW_SIZES = {
        'thumbnail': (200, 200),
        'medium': (800, 800),
        'large': (1200, 1200)
    }