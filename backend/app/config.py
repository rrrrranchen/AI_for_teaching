import os

class Config:
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads/teachingresources')
    PREVIEW_FOLDER = os.path.join(os.getcwd(), 'static/previews')
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx', 'jpg', 'png', 'mp4', 'mp3'}
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    
    # 预览图尺寸配置
    PREVIEW_SIZES = {
        'thumbnail': (200, 200),
        'medium': (800, 800),
        'large': (1200, 1200)
    }