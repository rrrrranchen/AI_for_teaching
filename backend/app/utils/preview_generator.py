import os
from PIL import Image
from pdf2image import convert_from_path
import subprocess
from typing import Dict, Optional
from flask import current_app
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW_FOLDER = os.path.join(project_root, 'static', 'uploads','preview')
def generate_preview(
    filepath: str, 
    unique_id: str,
    sizes: Optional[Dict[str, tuple]] = None
) -> Dict[str, str]:
    """
    生成多种尺寸的预览图
    
    Args:
        filepath: 源文件路径
        unique_id: 唯一标识符
        sizes: 预览尺寸配置 {'thumb': (200,200), 'medium': (800,800)}
    
    Returns:
        预览图URL字典 {'thumbnail': '/previews/xxx_thumb.jpg'}
    """
    if sizes is None:
        sizes = {
            'thumbnail': (200, 200),
            'medium': (800, 800),
            'large': (1200, 1200)
        }
    
    preview_dir = PREVIEW_FOLDER
    os.makedirs(preview_dir, exist_ok=True)
    ext = os.path.splitext(filepath)[1][1:].lower()
    previews = {}
    
    try:
        # 图片文件处理
        if ext in ['jpg', 'jpeg', 'png']:
            with Image.open(filepath) as img:
                for name, size in sizes.items():
                    output_path = os.path.join(preview_dir, f"{unique_id}_{name}.jpg")
                    _generate_image_preview(img, output_path, size)
                    previews[name] = f"/previews/{unique_id}_{name}.jpg"
        
        # PDF文件处理
        elif ext == 'pdf':
            for name, size in sizes.items():
                output_path = os.path.join(preview_dir, f"{unique_id}_{name}.jpg")
                _generate_pdf_preview(filepath, output_path, size)
                previews[name] = f"/previews/{unique_id}_{name}.jpg"
        
        # 视频文件处理
        elif ext == 'mp4':
            output_path = os.path.join(preview_dir, f"{unique_id}_thumbnail.jpg")
            _generate_video_preview(filepath, output_path)
            previews['thumbnail'] = f"/previews/{unique_id}_thumbnail.jpg"
    
    except Exception as e:
        current_app.logger.error(f"预览生成失败: {str(e)}")
    
    # 默认预览图
    if not previews:
        previews['thumbnail'] = '/static/default_preview.jpg'
    
    return previews

def _generate_image_preview(img: Image.Image, output_path: str, size: tuple):
    """生成图片预览"""
    img.thumbnail(size)
    img.save(output_path, 'JPEG', quality=85)

def _generate_pdf_preview(pdf_path: str, output_path: str, size: tuple):
    """生成PDF预览"""
    images = convert_from_path(
        pdf_path,
        first_page=1,
        last_page=1,
        size=size[0]
    )
    images[0].save(output_path, 'JPEG', quality=85)

def _generate_video_preview(video_path: str, output_path: str):
    """生成视频缩略图（使用FFmpeg）"""
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-ss', '00:00:01',
        '-vframes', '1',
        '-vf', 'scale=320:-1',
        '-y',  # 覆盖输出文件
        output_path
    ]
    subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True
    )