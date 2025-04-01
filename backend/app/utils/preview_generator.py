import os
from typing import Dict, Optional
from PIL import Image, ImageOps, ImageFilter
from pdf2image import convert_from_path
import subprocess
from flask import current_app

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW_FOLDER = os.path.join(project_root, 'static', 'uploads', 'preview')

def generate_preview(
    filepath: str, 
    unique_id: str,
    sizes: Optional[Dict[str, tuple]] = None
) -> Dict[str, str]:
    """
    生成多种尺寸的预览图（修复迭代错误版）
    """
    if sizes is None:
        sizes = {
            'thumbnail': (200, 200),
            'medium': (800, 800),
            'large': (1200, 1200)
        }
    
    os.makedirs(PREVIEW_FOLDER, exist_ok=True)
    ext = os.path.splitext(filepath)[1][1:].lower()
    previews = {}
    
    try:
        # 图片文件处理
        if ext in {'jpg', 'jpeg', 'png', 'webp'}:
            with Image.open(filepath) as img:
                img = ImageOps.exif_transpose(img)
                for name in sizes.keys():  # 提前遍历尺寸配置
                    output_path = os.path.join(
                        PREVIEW_FOLDER, 
                        f"{unique_id}_{name}.jpg"
                    )
                    success = _generate_image_preview(img.copy(), output_path, sizes[name])
                    if success:
                        previews[name] = f"/previews/{unique_id}_{name}.jpg"

        # PDF文件处理
        elif ext == 'pdf':
            try:
                images = convert_from_path(
                    filepath,
                    first_page=1,
                    last_page=1,
                    fmt='jpeg',
                    thread_count=2
                )
                for name in sizes.keys():
                    output_path = os.path.join(
                        PREVIEW_FOLDER, 
                        f"{unique_id}_{name}.jpg"
                    )
                    if _generate_pdf_preview(images[0].copy(), output_path, sizes[name]):
                        previews[name] = f"/previews/{unique_id}_{name}.jpg"
            except Exception as pdf_error:
                current_app.logger.error(f"PDF处理失败: {str(pdf_error)}")

        # 视频文件处理
        elif ext in {'mp4', 'mov', 'avi'}:
            output_path = os.path.join(
                PREVIEW_FOLDER, 
                f"{unique_id}_thumbnail.jpg"
            )
            if _generate_video_preview(filepath, output_path):
                previews['thumbnail'] = f"/previews/{unique_id}_thumbnail.jpg"

    except Exception as e:
        current_app.logger.error(f"预览生成失败: {str(e)}", exc_info=True)
        _cleanup_previews(unique_id, sizes.keys())

    # 添加尺寸元数据（安全方式）
    metadata = {}
    for name in sizes.keys():
        if name in previews:
            metadata.update({
                f"{name}_width": sizes[name][0],
                f"{name}_height": sizes[name][1]
            })
    
    # 合并结果
    final_previews = {'thumbnail': '/static/default_preview.jpg'} if not previews else previews
    final_previews.update(metadata)
    
    return final_previews

def _generate_image_preview(img: Image.Image, output_path: str, size: tuple) -> bool:
    """生成图片预览并返回是否成功"""
    try:
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(output_path, 'JPEG', quality=85, optimize=True)
        return True
    except Exception as e:
        current_app.logger.error(f"图片处理失败: {str(e)}")
        return False

def _generate_pdf_preview(pdf_image: Image.Image, output_path: str, size: tuple) -> bool:
    """生成PDF预览"""
    try:
        pdf_image.thumbnail(size, Image.Resampling.LANCZOS)
        pdf_image.save(output_path, 'JPEG', quality=85)
        return True
    except Exception as e:
        current_app.logger.error(f"PDF预览生成失败: {str(e)}")
        return False

def _generate_video_preview(video_path: str, output_path: str) -> bool:
    """生成视频缩略图并返回是否成功"""
    try:
        cmd = [
            'ffmpeg', '-i', video_path,
            '-ss', '00:00:01', '-vframes', '1',
            '-vf', 'scale=320:-1', '-y', output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return os.path.exists(output_path)
    except Exception as e:
        current_app.logger.error(f"视频处理失败: {str(e)}")
        return False

def _cleanup_previews(unique_id: str, size_names: list):
    """清理可能生成的不完整文件"""
    for name in size_names:
        preview_path = os.path.join(
            PREVIEW_FOLDER, 
            f"{unique_id}_{name}.jpg"
        )
        if os.path.exists(preview_path):
            os.remove(preview_path)
    thumbnail_path = os.path.join(
        PREVIEW_FOLDER, 
        f"{unique_id}_thumbnail.jpg"
    )
    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)