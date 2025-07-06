import os
import shutil
import uuid
import chardet
import markdown
import pandas as pd
from datetime import datetime
import time
from werkzeug.utils import secure_filename
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings
from llama_index.core.schema import TextNode
from llama_index.core import SimpleDirectoryReader
from app.models.relationship import category_knowledge_base
from llama_index.embeddings.dashscope import (
    DashScopeEmbedding,
    DashScopeTextEmbeddingModels,
    DashScopeTextEmbeddingType,
)
from llama_index.core.node_parser import SentenceSplitter
from typing import List, Optional
# 配置常量
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER_KNOWLEDGE=os.path.join(project_root,'static','knowledge')
DB_PATH = os.path.join(UPLOAD_FOLDER_KNOWLEDGE,'base')  # 知识库向量存储路径

# 设置嵌入模型
EMBED_MODEL = DashScopeEmbedding(
    model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V2,
    text_type=DashScopeTextEmbeddingType.TEXT_TYPE_DOCUMENT,
)
Settings.embed_model = EMBED_MODEL

# 允许的文件类型
ALLOWED_STRUCTURAL_EXTENSIONS = {'csv', 'xlsx', 'xls'}
ALLOWED_NON_STRUCTURAL_EXTENSIONS = {'txt','md','doc','docx','pdf','html','htm','ppt','pptx'}

from llama_index.embeddings.dashscope import DashScopeEmbedding


def allowed_file_structural(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_STRUCTURAL_EXTENSIONS

def allowed_file_non_structural(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_NON_STRUCTURAL_EXTENSIONS

def ensure_directories_exist():
    """确保必要的目录存在"""
    os.makedirs(UPLOAD_FOLDER_KNOWLEDGE, exist_ok=True)
    os.makedirs(DB_PATH, exist_ok=True)

def create_user_category_folder(user_id: int, category_id: int) -> str:
    """创建用户类目文件夹，并返回文件夹路径"""
    folder_name = f"user_{user_id}_category_{category_id}"
    folder_path = os.path.join(UPLOAD_FOLDER_KNOWLEDGE, 'category', folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    relative_path = os.path.join('static', 'knowledge', 'category', folder_name)
    return relative_path

def create_knowledge_base_folder(knowledge_base_id: int) -> str:
    """创建知识库文件夹，并返回文件夹路径"""
    folder_name = f"knowledge_base_{knowledge_base_id}"
    folder_path = os.path.join(UPLOAD_FOLDER_KNOWLEDGE, 'base', folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    relative_path = os.path.join('static', 'knowledge', 'base', folder_name)
    return relative_path

def upload_file_to_folder_structural(file, folder_path: str) -> str:
    """上传结构化文件到指定文件夹，并返回文件路径"""
    if file and allowed_file_structural(file.filename):
        filename=file.filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(folder_path, unique_filename)
        o_file_path = os.path.join(project_root,'static','knowledge','originalfiles',unique_filename)
        file.save(file_path)
        file.save(o_file_path)
        # 转换结构化数据为文本
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(file_path)
        elif filename.endswith(".csv"):
            df = pd.read_csv(file_path)
        
        # 生成文本文件
        txt_filename = os.path.splitext(unique_filename)[0] + '.txt'
        txt_filepath = os.path.join(folder_path, txt_filename)
        with open(txt_filepath, "w", encoding='utf-8') as f:
            for idx, row in df.iterrows():
                info = [f"{col}:{row[col]}" for col in df.columns]
                f.write("【" + ",".join(info) + "】\n")
        
        # 删除原始文件，只保留转换后的文本文件
        os.remove(file_path)
        
        # 返回相对于静态目录的路径
        relative_path = os.path.join('static', 'knowledge', 'category', os.path.basename(folder_path), txt_filename)
        o_relative_path= os.path.join('static','knowledge','originalfiles',unique_filename)
        return relative_path,o_relative_path
    else:
        raise ValueError("不支持的结构化文件类型")
   # 从配置中获取Mineru的API Token


import oss2
import os
import zipfile
import tempfile
import requests
from typing import Tuple

# OSS配置 (建议从环境变量或配置文件中读取)
OSS_CONFIG = {
    'endpoint': 'oss-cn-chengdu.aliyuncs.com',
    'access_key_id': os.getenv('ALIYUN_ACCESS_KEY_ID'),
    'access_key_secret': os.getenv('ALIYUN_ACCESS_KEY_SECRET'),
    'bucket_name': 'knowledge-file12',
    'public_domain': 'https://knowledge-file12.oss-cn-chengdu.aliyuncs.com'
}

class OSSHelper:
    def __init__(self):
        
        auth = oss2.Auth(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
        self.bucket = oss2.Bucket(auth, OSS_CONFIG['endpoint'], OSS_CONFIG['bucket_name'])
    
    def upload_file(self, file_path: str, object_name: str = None) -> Tuple[str, str]:
        """
        上传文件到OSS
        :param file_path: 本地文件路径
        :param object_name: OSS对象名(不包含bucket名)，如果None则自动生成
        :return: (public_url, object_name)
        """
        if not object_name:
            # 生成唯一的对象名: 日期/uuid_原文件名
            file_name = os.path.basename(file_path)
            object_name = f"{datetime.now().strftime('%Y%m%d')}/{str(uuid.uuid4())}_{file_name}"
        
        try:
            with open(file_path, 'rb') as file:
                self.bucket.put_object(object_name, file)
            
            public_url = f"{OSS_CONFIG['public_domain']}/{object_name}"
            return public_url, object_name
        except Exception as e:
            raise RuntimeError(f"OSS上传失败: {e}")
    
    def download_file(self, object_name: str, local_path: str = None) -> str:
        """
        从OSS下载文件
        :param object_name: OSS对象名
        :param local_path: 本地存储路径，如果None则使用临时文件
        :return: 本地文件路径
        """
        if not local_path:
            # 创建临时文件
            temp_dir = tempfile.mkdtemp()
            file_name = os.path.basename(object_name)
            local_path = os.path.join(temp_dir, file_name)
        
        try:
            self.bucket.get_object_to_file(object_name, local_path)
            return local_path
        except Exception as e:
            raise RuntimeError(f"OSS下载失败: {e}")
    
    def delete_file(self, object_name: str):
        """删除OSS文件"""
        try:
            self.bucket.delete_object(object_name)
        except Exception as e:
            print(f"OSS文件删除失败(可忽略): {e}")

# 全局OSS助手实例
oss_helper = OSSHelper()
MINERU_API_TOKEN='eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI4NjMwMDg1MSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc1MTUyMzYyMiwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTUwNTAxMjU2NjAiLCJvcGVuSWQiOm51bGwsInV1aWQiOiIwYmIxYjRlMi0wMjc5LTQ4MzgtOGI2MC1iNDVhNmU3Y2Y4MWQiLCJlbWFpbCI6IiIsImV4cCI6MTc1MjczMzIyMn0.ebk7ZczL0BK64f7ZVtYr4gSf6IixaBAn801Oh7tP2xW61O9uwUOFAax7yxXlx5uPcb3dh8gncbhFOavaFWr5AQ'
def upload_to_cdn(file_path: str) -> str:
    """上传文件到OSS并返回公开URL"""
    try:
        public_url, _ = oss_helper.upload_file(file_path)
        return public_url
    except Exception as e:
        print(f"文件上传CDN失败: {e}")
        raise RuntimeError("文件上传CDN失败")

def download_and_extract(zip_url: str, target_dir: str) -> Tuple[str, List[str]]:
    """
    下载并解压Mineru返回的ZIP文件，提取Markdown文件和图片
    
    :param zip_url: Mineru返回的zip文件URL(来自其自己的CDN)
    :param target_dir: 解压目标目录
    :return: 元组 (Markdown文件路径, 图片文件路径列表)
    :raises: RuntimeError 如果处理失败
    """
    temp_dir = None
    try:
        # 1. 创建临时目录
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "mineru_result.zip")
        
        # 2. 下载ZIP文件
        response = requests.get(zip_url, stream=True)
        response.raise_for_status()
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 3. 解压ZIP文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 4. 查找Markdown文件和图片
        md_files = []
        image_files = []
        
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith('.md'):
                    md_files.append(file_path)
                elif file.lower().split('.')[-1] in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                    image_files.append(file_path)
        
        if not md_files:
            raise RuntimeError("ZIP文件中未找到Markdown文件")
        
        # 5. 创建目标目录结构
        os.makedirs(target_dir, exist_ok=True)
        images_dir = os.path.join(project_root,'static','knowledge','fileimages')
        os.makedirs(images_dir, exist_ok=True)
        
        # 6. 移动Markdown文件到目标目录
        src_md_path = md_files[0]
        md_filename = os.path.basename(src_md_path)
        dest_md_path = os.path.join(target_dir, md_filename)
        shutil.move(src_md_path, dest_md_path)
        
        # 7. 移动图片文件到fileimages目录
        dest_image_paths = []
        for img_path in image_files:
            img_filename = os.path.basename(img_path)
            dest_img_path = os.path.join(images_dir, img_filename)
            
            # 处理文件名冲突
            counter = 1
            while os.path.exists(dest_img_path):
                name, ext = os.path.splitext(img_filename)
                dest_img_path = os.path.join(images_dir, f"{name}_{counter}{ext}")
                counter += 1
            
            shutil.move(img_path, dest_img_path)
            dest_image_paths.append(dest_img_path)
        
        return dest_md_path, dest_image_paths
        
    except Exception as e:
        print(f"下载解压失败: {e}")
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise RuntimeError(f"Mineru结果处理失败: {str(e)}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
# Mineru API配置
MINERU_API_URL = "https://mineru.net/api/v4/extract/task"
MINERU_RESULT_URL = "https://mineru.net/api/v4/extract/task/{task_id}"

# def upload_file_to_folder_non_structural(file, folder_path: str) -> Tuple[str, List[str], str]:
#     """上传非结构化文件并转换为TXT存储
    
#     Args:
#         file: 上传的文件对象
#         folder_path: 存储文件的目录路径
        
#     Returns:
#         元组 (TXT文件相对路径, 图片文件相对路径列表, 原始文件相对路径)
        
#     Raises:
#         ValueError: 文件类型不支持
#         RuntimeError: 文件处理失败
#     """
#     if not (file and allowed_file_non_structural(file.filename)):
#         raise ValueError("不支持的非结构化文件类型")
    
#     try:
#         # 保存原始文件
#         unique_filename = f"{uuid.uuid4()}_{file.filename}"
#         file_path = os.path.join(folder_path, unique_filename)
#         originalfile_path = os.path.join(project_root, 'static', 'knowledge', 'originalfiles', unique_filename)
#         r_originalfile_path = os.path.join('static', 'knowledge', 'originalfiles', unique_filename)
        
#         # 确保目录存在
#         os.makedirs(os.path.dirname(originalfile_path), exist_ok=True)
#         file.save(file_path)
#         file.save(originalfile_path)
        
#         # 获取文件扩展名
#         file_ext = file.filename.split('.')[-1].lower()
        
#         # 对于txt、md、html、htm文件，直接处理
#         if file_ext in ['txt', 'md', 'html', 'htm']:
#             # 1. 读取文件内容（自动处理编码）
#             with open(file_path, 'rb') as f:
#                 raw_data = f.read()
#                 encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            
#             # 2. 转换内容为纯文本
#             content = raw_data.decode(encoding)
            
#             # 如果是markdown文件，转换为纯文本
#             if file_ext == 'md':
#                 content = markdown.markdown(content)  # 先转换为HTML
#                 # 移除HTML标签
#                 content = re.sub(r'<[^>]+>', '', content)
            
#             # 如果是HTML文件，移除标签
#             elif file_ext in ['html', 'htm']:
#                 content = re.sub(r'<[^>]+>', '', content)
            
#             # 3. 生成TXT文件名
#             txt_filename = os.path.splitext(unique_filename)[0] + '.txt'
#             txt_filepath = os.path.join(folder_path, txt_filename)
            
#             # 4. 写入TXT文件
#             with open(txt_filepath, 'w', encoding='utf-8') as f:
#                 f.write(content)
            
#             # 5. 构建返回路径
#             txt_relative_path = os.path.join('static', 'knowledge', 'category', 
#                                            os.path.basename(folder_path), txt_filename)
            
#             # 6. 清理临时文件
#             os.remove(file_path)
            
#             return txt_relative_path, [], r_originalfile_path
        
#         # 对于其他文件类型，仍然使用Mineru处理
#         else:
#             # 步骤1: 将文件上传到公共可访问的URL
#             public_url = upload_to_cdn(file_path)  
            
#             # 步骤2: 调用Mineru API解析文件
#             task_id = create_mineru_task(public_url)
#             if not task_id:
#                 raise RuntimeError("Mineru任务创建失败")
            
#             # 步骤3: 轮询获取解析结果
#             zip_url = poll_mineru_result(task_id)
#             if not zip_url:
#                 raise RuntimeError("Mineru解析失败")
            
#             # 步骤4: 下载并解压结果，获取Markdown文件和图片
#             md_file_path, image_paths = download_and_extract(zip_url, folder_path)
            
#             # 步骤5: 将Markdown转换为TXT
#             txt_file_path = convert_md_to_txt(md_file_path)
            
#             # 构建相对路径
#             base_relative_path = os.path.join('static', 'knowledge', 'category', 
#                                             os.path.basename(folder_path))
            
#             # TXT文件相对路径
#             txt_relative_path = os.path.join(base_relative_path, 
#                                            os.path.basename(txt_file_path))
            
#             # 图片文件相对路径
#             image_relative_paths = []
#             for img_path in image_paths:
#                 rel_path = os.path.join('static', 'knowledge', 'fileimages',
#                                       os.path.basename(img_path))
#                 image_relative_paths.append(rel_path)
            
#             # 清理临时文件
#             os.remove(file_path)  # 删除原始文件
#             os.remove(md_file_path)  # 删除Markdown文件
            
#             return txt_relative_path, image_relative_paths, r_originalfile_path
            
#     except Exception as e:
#         # 清理可能存在的临时文件
#         if 'file_path' in locals() and os.path.exists(file_path):
#             os.remove(file_path)
#         if 'md_file_path' in locals() and os.path.exists(md_file_path):
#             os.remove(md_file_path)
#         raise RuntimeError(f"文件处理失败: {str(e)}")

def upload_file_to_folder_non_structural(file, folder_path: str) -> Tuple[str, List[str], str]:
    """上传非结构化文件并保留原始格式存储
    
    Args:
        file: 上传的文件对象
        folder_path: 存储文件的目录路径
        
    Returns:
        元组 (文件相对路径, 图片文件相对路径列表, 原始文件相对路径)
        
    Raises:
        ValueError: 文件类型不支持
        RuntimeError: 文件处理失败
    """
    if not (file and allowed_file_non_structural(file.filename)):
        raise ValueError("不支持的非结构化文件类型")
    
    try:
        # 生成唯一文件名
        unique_id = uuid.uuid4()
        original_filename = file.filename
        file_ext = original_filename.split('.')[-1].lower()
        unique_filename = f"{unique_id}_{original_filename}"
        
        # 保存原始文件
        file_path = os.path.join(folder_path, unique_filename)
        originalfile_path = os.path.join(project_root, 'static', 'knowledge', 'originalfiles', unique_filename)
        r_originalfile_path = os.path.join('static', 'knowledge', 'originalfiles', unique_filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(originalfile_path), exist_ok=True)
        file.save(file_path)
        file.save(originalfile_path)
        
        # 对于txt、md、html、htm文件，直接处理
        if file_ext in ['txt', 'md', 'html', 'htm']:
            # 1. 读取文件内容（自动处理编码）
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
                content = raw_data.decode(encoding)
            
            # 2. 对于HTML文件，移除标签
            if file_ext in ['html', 'htm']:
                content = re.sub(r'<[^>]+>', '', content)
                # 保存为TXT文件
                processed_filename = f"{unique_id}.txt"
                processed_filepath = os.path.join(folder_path, processed_filename)
                with open(processed_filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                # 更新返回路径
                relative_path = os.path.join('static', 'knowledge', 'category', 
                                           os.path.basename(folder_path), processed_filename)
                # 清理临时文件
                os.remove(file_path)
                return relative_path, [], r_originalfile_path
            else:
                # 如果是MD文件，转换其中的图片路径
                if file_ext == 'md':
                    content = convert_md_image_paths(content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                # 对于txt和md文件，直接使用原文件（但确保文件名唯一）
                relative_path = os.path.join('static', 'knowledge', 'category', 
                                           os.path.basename(folder_path), unique_filename)
                return relative_path, [], r_originalfile_path
        
        # 对于其他文件类型，仍然使用Mineru处理
        else:
            # 步骤1: 将文件上传到公共可访问的URL
            public_url = upload_to_cdn(file_path)  
            
            # 步骤2: 调用Mineru API解析文件
            task_id = create_mineru_task(public_url)
            if not task_id:
                raise RuntimeError("Mineru任务创建失败")
            
            # 步骤3: 轮询获取解析结果
            zip_url = poll_mineru_result(task_id)
            if not zip_url:
                raise RuntimeError("Mineru解析失败")
            
            # 步骤4: 下载并解压结果，获取Markdown文件和图片
            md_file_path, image_paths = download_and_extract(zip_url, folder_path)
            
            # 读取并转换Markdown文件中的图片路径
            with open(md_file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            md_content = convert_md_image_paths(md_content)
            
            # 为MD文件生成唯一名称
            md_unique_filename = f"{unique_id}.md"
            md_unique_path = os.path.join(folder_path, md_unique_filename)
            with open(md_unique_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            os.remove(md_file_path)  # 删除原始Markdown文件
            
            # 构建相对路径
            base_relative_path = os.path.join('static', 'knowledge', 'category', 
                                            os.path.basename(folder_path))
            
            # MD文件相对路径
            md_relative_path = os.path.join(base_relative_path, md_unique_filename)
            
            # 图片文件相对路径（也确保唯一性）
            image_relative_paths = []
            for img_path in image_paths:
                rel_path = os.path.join('static', 'knowledge', 'fileimages', img_path)
                image_relative_paths.append(rel_path)
            
            # 清理临时文件
            os.remove(file_path)  # 删除原始文件
            
            return md_relative_path, image_relative_paths, r_originalfile_path
            
    except Exception as e:
        # 清理可能存在的临时文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        if 'md_file_path' in locals() and os.path.exists(md_file_path):
            os.remove(md_file_path)
        raise RuntimeError(f"文件处理失败: {str(e)}")


def convert_md_image_paths(md_content: str, base_url: str = "http://localhost:5000") -> str:
    """
    将Markdown内容中的图片相对路径转换为完整URL路径
    
    参数:
        md_content: Markdown文本内容
        base_url: 基础URL地址，默认为"http://localhost:5000"
        
    返回:
        转换后的Markdown内容
    
    功能:
        将类似 ![](images/xxx.jpg) 的路径转换为
        ![](http://localhost:5000/static/knowledge/fileimages/xxx.jpg)
    """
    # 定义匹配Markdown图片的正则表达式
    pattern = r'!\[(.*?)\]\((images/.*?)\)'
    
    def replace_path(match):
        alt_text = match.group(1)  # 获取图片描述文本
        img_name = match.group(2).split('/')[-1]  # 提取图片文件名
        # 构建新的图片URL路径
        new_path = f"{base_url}/static/knowledge/fileimages/{img_name}"
        return f'![{alt_text}]({new_path})'
    
    # 执行替换
    return re.sub(pattern, replace_path, md_content)

def create_mineru_task(file_url: str) -> Optional[str]:
    """创建Mineru解析任务"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {MINERU_API_TOKEN}'
    }
    payload = {
        "url": file_url,
        "is_ocr": True,
        "enable_formula": False,
        "enable_table": True,
        "language": "ch",
        
    }
    
    try:
        response = requests.post(MINERU_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["data"]["task_id"]
    except Exception as e:
        print(f"Mineru任务创建失败: {e}")
        return None

def poll_mineru_result(task_id: str, max_retries=1000, interval=3) -> Optional[str]:
    """轮询获取Mineru解析结果"""
    headers = {'Authorization': f'Bearer {MINERU_API_TOKEN}'}
    url = MINERU_RESULT_URL.format(task_id=task_id)
    
    for _ in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()["data"]
            
            if data["state"] == "done":
                return data["full_zip_url"]
            elif data["state"] in ("failed", "error"):
                print(f"解析失败: {data.get('err_msg', '未知错误')}")
                return None
            
            # 解析中，等待下次轮询
            time.sleep(interval)
            print("轮询中")
            
        except Exception as e:
            print(f"轮询失败: {e}")
            time.sleep(interval)
    
    print("解析超时")
    return None

import re
import os
from typing import Optional

def convert_md_to_txt(md_file_path: str) -> Optional[str]:
    """
    将Markdown文件转换为纯文本文件，保留所有原始内容和格式
    
    参数:
        md_file_path: Markdown文件路径
        
    返回:
        生成的txt文件路径，如果失败则返回None
    """
    try:
        # 1. 读取Markdown文件（自动处理编码）
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 2. 生成唯一文件名
        base_name = os.path.splitext(os.path.basename(md_file_path))[0]
        unique_id = str(uuid.uuid4())[:8]  # 取前8位
        txt_file_name = f"{base_name}_{unique_id}.txt"
        txt_file_path = os.path.join(os.path.dirname(md_file_path), txt_file_name)
        
        # 3. 直接写入原始Markdown内容（保留所有格式）
        with open(txt_file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return txt_file_path
    except UnicodeDecodeError:
        # 如果UTF-8失败，尝试自动检测编码
        try:
            import chardet
            with open(md_file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            
            with open(md_file_path, 'r', encoding=encoding) as f:
                md_content = f.read()
            
            with open(txt_file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            return txt_file_path
        except Exception as e:
            print(f"转换失败(编码问题): {e}")
            return None
    except Exception as e:
        print(f"转换失败: {e}")
        return None