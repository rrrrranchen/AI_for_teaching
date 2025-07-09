from http import HTTPStatus
import os
import shutil
from fastapi import logger
from flask import current_app
from llama_index.core import VectorStoreIndex, Settings, SimpleDirectoryReader
from llama_index.embeddings.dashscope import (
    DashScopeEmbedding,
    DashScopeTextEmbeddingModels,
    DashScopeTextEmbeddingType,
)
from app.config import Config
from llama_index.core.schema import TextNode, Document
from llama_index.core.node_parser import SentenceSplitter

# 配置嵌入模型（添加批处理大小限制）
EMBED_MODEL = DashScopeEmbedding(
    model_name="text-embedding-v4",
    text_type=DashScopeTextEmbeddingType.TEXT_TYPE_DOCUMENT,
    embed_batch_size=8  
)

Settings.embed_model = EMBED_MODEL
Settings.chunk_overlap = 50

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORY_PATH = os.path.join(project_root, 'static', 'knowledge', 'category')
BASE_PATH = os.path.join(project_root, 'static', 'knowledge', 'base')

def list_knowledge_bases():
    """List all existing knowledge bases"""
    return [name for name in os.listdir(BASE_PATH) 
            if os.path.isdir(os.path.join(BASE_PATH, name))]

def create_unstructured_db(db_name: str, label_name: list):
    """创建非结构化知识库索引（优化Markdown分块，确保格式完整）"""
    print(f"知识库名称为：{db_name}，类目名称为：{label_name}")
    
    # 验证输入
    if not label_name:
        print("没有选择类目")
        return
    elif len(db_name) == 0:
        print("没有命名知识库")
        return
    elif db_name in os.listdir(BASE_PATH):
        print("知识库已存在，请换个名字或删除原来知识库再创建")
        return
    
    # 初始化文档处理器
    node_parser = SentenceSplitter(
        chunk_overlap=Settings.chunk_overlap,
        chunk_size=3000
    )
    
    def optimized_markdown_split(content: str) -> list[str]:
        """优化Markdown分块逻辑，确保格式完整"""
        chunks = []
        current_chunk = []
        current_length = 0
        in_code_block = False  # 标记是否在代码块中
        in_list = False  # 标记是否在列表中
        
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped_line = line.strip()
            line_length = len(line)
            
            # 检测代码块开始/结束
            if stripped_line.startswith('```'):
                in_code_block = not in_code_block
            
            # 检测列表项
            is_list_item = stripped_line.startswith(('- ', '* ', '+ ')) or \
                           (stripped_line[0].isdigit() and stripped_line[1] == '.') if stripped_line else False
            
            # 处理在代码块中的行（保持代码块完整）
            if in_code_block:
                current_chunk.append(line)
                current_length += line_length + 1  # +1 for newline
                i += 1
                continue
            
            # 处理超长行（如长URL或代码）
            if line_length > 3000 and not in_code_block:
                # 在空格处分割长行，避免破坏单词
                while len(line) > 3000:
                    split_index = line[:3000].rfind(' ')
                    if split_index == -1 or split_index < 1000:  # 找不到合适分割点
                        split_index = 3000
                    chunks.append(line[:split_index])
                    line = line[split_index:].lstrip()
                current_chunk = [line]
                current_length = len(line)
                i += 1
                continue
            
            # 处理标题行（保持标题与内容完整）
            if stripped_line.startswith('#') and not in_code_block:
                # 保存当前块（如果有内容）
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:
                        chunks.append(chunk_text)
                    current_chunk = []
                    current_length = 0
                
                # 收集标题及后续相关内容
                section_lines = [line]
                section_length = line_length
                
                # 添加后续内容直到达到块大小或遇到新标题
                j = i + 1
                while j < len(lines) and section_length < 2500:  # 留缓冲空间
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    
                    # 遇到新标题或代码块开始则停止
                    if next_stripped.startswith('#') or next_stripped.startswith('```'):
                        break
                    
                    section_lines.append(next_line)
                    section_length += len(next_line) + 1  # +1 for newline
                    j += 1
                
                # 添加标题块
                chunk_text = '\n'.join(section_lines).strip()
                if chunk_text:
                    chunks.append(chunk_text)
                i = j  # 跳过已处理的行
                continue
            
            # 处理列表项（保持列表完整）
            if is_list_item:
                if in_list and current_length + line_length > 3000:
                    # 当前块已满，保存并开始新块
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:
                        chunks.append(chunk_text)
                    current_chunk = [line]
                    current_length = line_length
                else:
                    # 继续当前列表
                    current_chunk.append(line)
                    current_length += line_length + 1  # +1 for newline
                    in_list = True
                i += 1
                continue
            else:
                in_list = False  # 退出列表状态
            
            # 普通行处理
            if current_length + line_length <= 3000:
                current_chunk.append(line)
                current_length += line_length + 1  # +1 for newline
                i += 1
            else:
                # 当前块已满，保存并开始新块
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:
                        chunks.append(chunk_text)
                
                current_chunk = [line]
                current_length = line_length
                i += 1
        
        # 处理最后一个块
        if current_chunk:
            chunk_text = '\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)
        
        # 合并过小的块（智能合并）
        merged_chunks = []
        for chunk in chunks:
            # 确保不超过8192限制
            while len(chunk) > 8192:
                # 在段落边界处分割
                split_index = chunk[:8192].rfind('\n\n')
                if split_index == -1:
                    split_index = chunk[:8192].rfind('\n')
                if split_index == -1 or split_index < 1000:  # 找不到合适分割点
                    split_index = 8192
                
                merged_chunks.append(chunk[:split_index].strip())
                chunk = chunk[split_index:].lstrip()
            
            if not merged_chunks:
                merged_chunks.append(chunk)
            else:
                last_chunk = merged_chunks[-1]
                # 只在内容相关时合并（如两者都是文本或都是列表）
                last_is_text = not last_chunk.strip().startswith(('#', '-', '*', '+')) or \
                              any(char.isalpha() for char in last_chunk)
                current_is_text = not chunk.strip().startswith(('#', '-', '*', '+')) or \
                                 any(char.isalpha() for char in chunk)
                
                if (last_is_text and current_is_text) and \
                   len(last_chunk) + len(chunk) + 2 <= 8192:  # +2为换行符
                    merged_chunks[-1] = last_chunk + '\n\n' + chunk
                else:
                    merged_chunks.append(chunk)
        
        return merged_chunks
    
    documents = []
    for label in label_name:
        label_path = os.path.join(CATEGORY_PATH, label)
        if not os.path.exists(label_path):
            continue
            
        # 获取目录下所有文件
        file_paths = []
        for root, _, files in os.walk(label_path):
            for file in files:
                file_path = os.path.join(root, file)
                # 跳过隐藏文件和系统文件
                if not file.startswith('.') and not file.startswith('~$'):
                    file_paths.append(file_path)
        
        for file_path in file_paths:
            # 获取文件扩展名
            file_ext = os.path.splitext(file_path)[1].lower()
            
            try:
                # 检查文件大小
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:  # 10MB
                    print(f"文件 {file_path} 过大({file_size/1024/1024:.2f}MB)，跳过处理")
                    continue
                
                # 读取文件内容
                if file_ext == '.md':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 跳过空文件
                    if not content.strip():
                        print(f"文件 {file_path} 内容为空，跳过处理")
                        continue
                    
                    # 创建基础元数据
                    base_metadata = {
                        'file_name': os.path.basename(file_path),
                        'file_path': file_path,
                        'db_name': db_name,
                        'category': label,
                        'data_type': 'unstructured'
                    }
                    
                    # 优化后的Markdown分块处理
                    chunks = optimized_markdown_split(content)
                    
                    for chunk in chunks:
                        # 复制元数据，避免引用问题
                        chunk_metadata = base_metadata.copy()
                        
                        # 检查是否包含图片
                        chunk_metadata['has_image'] = any(
                            tag in chunk for tag in ['![', '<img', '! [', '图像：']
                        )
                        
                        # 检查是否包含代码块
                        chunk_metadata['has_code'] = '```' in chunk
                        
                        document = Document(
                            text=chunk,
                            metadata=chunk_metadata,
                            id_=f"{os.path.basename(file_path)}_{hash(chunk)}"
                        )
                        documents.append(document)
                else:
                    # 其他文件类型使用SimpleDirectoryReader处理
                    reader = SimpleDirectoryReader(input_files=[file_path])
                    docs = reader.load_data()
                    for doc in docs:
                        # 添加元数据
                        doc.metadata.update({
                            'db_name': db_name,
                            'category': label,
                            'data_type': 'unstructured',
                            'has_image': False,
                            'has_code': False
                        })
                        # 分块处理
                        nodes = node_parser.get_nodes_from_documents([doc])
                        for node in nodes:
                            document = Document(
                                text=node.text,
                                metadata=node.metadata.copy(),
                                id_=node.id_
                            )
                            documents.append(document)
            except Exception as e:
                import traceback
                error_msg = f"处理文件 {file_path} 时出错: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                continue
    
    # 分批创建索引（每批最多100个节点）
    index = None
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        if index is None:
            index = VectorStoreIndex(batch)
        else:
            for document in batch:
                index.insert(document)
    
    # 保存索引
    if index:
        db_path = os.path.join(BASE_PATH, db_name)
        os.makedirs(db_path, exist_ok=True)
        index.storage_context.persist(db_path)
        print(f"知识库 {db_name} 创建成功，包含 {len(documents)} 个文档块")
    else:
        print("没有可处理的文档内容")



def create_structured_db(db_name: str, data_table: list):
    """创建结构化知识库索引（带批处理限制）"""
    print(f"知识库名称为：{db_name}，数据表名称为：{data_table}")
    
    # 验证输入
    if not data_table:
        print("没有选择数据表")
        return
    elif len(db_name) == 0:
        print("没有命名知识库")
        return
    elif db_name in os.listdir(BASE_PATH):
        print("知识库已存在，请换个名字或删除原来知识库再创建")
        return
    
    nodes = []
    for table in data_table:
        table_path = os.path.join(CATEGORY_PATH, table)
        if not os.path.exists(table_path):
            continue
            
        # 加载文档
        reader = SimpleDirectoryReader(table_path)
        docs = reader.load_data()
        
        for doc in docs:
            category = os.path.basename(table_path)
            file_name = doc.metadata.get('file_name', '')
            
            # 处理文档内容（按行分块）
            doc_content = doc.get_content().split('\n')
            for chunk in doc_content:
                if chunk.strip():
                    node = TextNode(text=chunk)
                    node.metadata = {
                        'db_name': db_name,
                        'category': category,
                        'file_name': file_name,
                        'file_path': doc.metadata.get('file_path', ''),
                        'data_type': 'structured'
                    }
                    # 将 TextNode 转换为 Document
                    document = Document(
                        text=node.text,
                        metadata=node.metadata,
                        id_=node.id_  # 如果 TextNode 有 id_ 属性，否则可以省略
                    )
                    nodes.append(document)
    
    # 分批创建索引
    index = None
    batch_size = 100
    for i in range(0, len(nodes), batch_size):
        batch = nodes[i:i+batch_size]
        if index is None:
            index = VectorStoreIndex(batch)
        else:
            for document in batch:
                index.insert(document)
    
    # 保存索引
    if index:
        db_path = os.path.join(BASE_PATH, db_name)
        os.makedirs(db_path, exist_ok=True)
        index.storage_context.persist(db_path)
        print(f"知识库 {db_name} 创建成功")
    else:
        print("没有可处理的文档内容")




# from http import HTTPStatus
# import os
# import shutil
# from fastapi import logger
# from flask import current_app
# from llama_index.core import VectorStoreIndex, Settings, SimpleDirectoryReader
# from llama_index.embeddings.dashscope import (
#     DashScopeEmbedding,
#     DashScopeTextEmbeddingModels,
#     DashScopeTextEmbeddingType,
# )
# from app.config import Config
# from llama_index.core.schema import TextNode, Document
# from llama_index.core.node_parser import SentenceSplitter
# import re

# # 配置嵌入模型（添加批处理大小限制）
# EMBED_MODEL = DashScopeEmbedding(
#     model_name="text-embedding-v4",
#     text_type=DashScopeTextEmbeddingType.TEXT_TYPE_DOCUMENT,
#     embed_batch_size=8
# )

# Settings.embed_model = EMBED_MODEL
# Settings.chunk_overlap = 50

# project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# CATEGORY_PATH = os.path.join(project_root, 'static', 'knowledge', 'category')
# BASE_PATH = os.path.join(project_root, 'static', 'knowledge', 'base')

# def safe_split_content(content: str, max_length: int = 8000) -> list[str]:
#     """
#     智能分割内容为多个段落，确保:
#     1. 保留所有原始内容
#     2. 每个段落不超过最大长度
#     3. 尽量在自然断点处分割
#     """
#     # 如果内容本身在安全范围内，直接返回
#     if len(content) <= max_length:
#         return [content]
    
#     chunks = []
#     current_chunk = ""
    
#     # 按段落分割（保留换行符）
#     paragraphs = re.split(r'(\n+)', content)
    
#     for paragraph in paragraphs:
#         # 如果当前段落为空则跳过
#         if not paragraph.strip():
#             continue
            
#         # 如果添加新段落不会超过限制
#         if len(current_chunk) + len(paragraph) <= max_length:
#             current_chunk += paragraph
#         else:
#             # 保存当前块
#             if current_chunk:
#                 chunks.append(current_chunk)
#                 current_chunk = ""
            
#             # 处理超长段落（超过max_length）
#             if len(paragraph) > max_length:
#                 # 在句子边界处分割超长段落
#                 sentences = re.split(r'(?<=[.!?。！？])\s+', paragraph)
#                 for sentence in sentences:
#                     if not sentence.strip():
#                         continue
                        
#                     if len(current_chunk) + len(sentence) <= max_length:
#                         current_chunk += sentence + " "
#                     else:
#                         if current_chunk:
#                             chunks.append(current_chunk.strip())
#                         current_chunk = sentence + " "
#             else:
#                 current_chunk = paragraph
    
#     # 添加最后一个块
#     if current_chunk:
#         chunks.append(current_chunk.strip())
    
#     # 确保所有块都符合长度要求
#     valid_chunks = []
#     for chunk in chunks:
#         if len(chunk) > max_length:
#             # 最后防线：按固定大小分割但保留完整单词
#             words = chunk.split()
#             current_line = ""
#             for word in words:
#                 if len(current_line) + len(word) + 1 <= max_length:
#                     current_line += word + " "
#                 else:
#                     if current_line:
#                         valid_chunks.append(current_line.strip())
#                     current_line = word + " "
#             if current_line:
#                 valid_chunks.append(current_line.strip())
#         else:
#             valid_chunks.append(chunk)
    
#     return valid_chunks

# def list_knowledge_bases():
#     """List all existing knowledge bases"""
#     return [name for name in os.listdir(BASE_PATH) 
#             if os.path.isdir(os.path.join(BASE_PATH, name))]

# def create_unstructured_db(db_name: str, label_name: list):
#     """创建非结构化知识库索引（优化Markdown分块，确保完整保留内容）"""
#     print(f"知识库名称为：{db_name}，类目名称为：{label_name}")
    
#     # 验证输入
#     if not label_name:
#         print("没有选择类目")
#         return
#     elif len(db_name) == 0:
#         print("没有命名知识库")
#         return
#     elif db_name in os.listdir(BASE_PATH):
#         print("知识库已存在，请换个名字或删除原来知识库再创建")
#         return
    
#     # 初始化文档处理器
#     node_parser = SentenceSplitter(
#         chunk_overlap=Settings.chunk_overlap,
#         chunk_size=3000
#     )
    
#     def optimized_markdown_split(content: str) -> list[str]:
#         """优化Markdown分块逻辑，保留完整内容"""
#         chunks = []
#         current_chunk = []
#         current_length = 0
        
#         # 按行处理
#         lines = content.split('\n')
#         i = 0
#         while i < len(lines):
#             line = lines[i]
#             stripped_line = line.strip()
#             line_length = len(line)
            
#             # 如果当前行是标题，尝试合并后续内容
#             if stripped_line.startswith('#'):
#                 # 收集标题及后续内容直到达到块大小
#                 section_lines = []
#                 section_length = 0
                
#                 # 添加标题行
#                 section_lines.append(line)
#                 section_length += line_length
                
#                 # 添加后续内容直到达到3000字符或遇到下一个标题
#                 j = i + 1
#                 while j < len(lines) and section_length < 2500:  # 留500字符缓冲
#                     next_line = lines[j]
#                     next_stripped = next_line.strip()
                    
#                     # 遇到新标题则停止
#                     if next_stripped.startswith('#'):
#                         break
                    
#                     section_lines.append(next_line)
#                     section_length += len(next_line)
#                     j += 1
                
#                 # 如果收集到的内容足够大，直接作为独立块
#                 if section_length >= 500:  # 最小有效块大小
#                     chunk_text = '\n'.join(section_lines)
#                     chunks.append(chunk_text)
#                     i = j  # 跳过已处理的行
#                     continue
#                 else:
#                     # 如果内容太小，添加到当前块
#                     current_chunk.extend(section_lines)
#                     current_length += section_length
#                     i = j
#                     continue
            
#             # 普通行处理
#             if current_length + line_length <= 3000:
#                 # 添加到当前块
#                 current_chunk.append(line)
#                 current_length += line_length
#                 i += 1
#             else:
#                 # 当前块已接近3000字符，保存当前块
#                 if current_chunk:
#                     chunk_text = '\n'.join(current_chunk).strip()
#                     if chunk_text:
#                         chunks.append(chunk_text)
                
#                 # 开始新块（除非当前行特别长）
#                 if line_length > 3000:
#                     # 处理超长行（如代码块）- 保留完整
#                     chunks.append(line)
#                     current_chunk = []
#                     current_length = 0
#                     i += 1
#                 else:
#                     current_chunk = [line]
#                     current_length = line_length
#                     i += 1
        
#         # 处理最后一个块
#         if current_chunk:
#             chunk_text = '\n'.join(current_chunk).strip()
#             if chunk_text:
#                 chunks.append(chunk_text)
        
#         # 合并过小的块
#         merged_chunks = []
#         for chunk in chunks:
#             if not merged_chunks or len(merged_chunks[-1]) + len(chunk) > 3000:
#                 # 开始新块
#                 merged_chunks.append(chunk)
#             else:
#                 # 合并到前一个块
#                 merged_chunks[-1] += '\n\n' + chunk
        
#         return merged_chunks
    
#     documents = []
#     for label in label_name:
#         label_path = os.path.join(CATEGORY_PATH, label)
#         if not os.path.exists(label_path):
#             continue
            
#         # 获取目录下所有文件
#         file_paths = []
#         for root, _, files in os.walk(label_path):
#             for file in files:
#                 file_paths.append(os.path.join(root, file))
        
#         for file_path in file_paths:
#             # 获取文件扩展名
#             file_ext = os.path.splitext(file_path)[1].lower()
            
#             try:
#                 # 读取文件内容
#                 if file_ext == '.md':
#                     with open(file_path, 'r', encoding='utf-8') as f:
#                         content = f.read()
                    
#                     # 创建基础元数据
#                     base_metadata = {
#                         'file_name': os.path.basename(file_path),
#                         'file_path': file_path,
#                         'db_name': db_name,
#                         'category': label,
#                         'data_type': 'unstructured'
#                     }
                    
#                     # 优化后的Markdown分块处理
#                     chunks = optimized_markdown_split(content)
                    
#                     for chunk in chunks:
#                         # 检查是否包含图片
#                         if '![' in chunk or '<img' in chunk:
#                             base_metadata['has_image'] = True
                        
#                         # 智能分割超长内容（确保不超过8000字符）
#                         safe_chunks = safe_split_content(chunk)
                        
#                         for idx, safe_chunk in enumerate(safe_chunks):
#                             document = Document(
#                                 text=safe_chunk,
#                                 metadata=base_metadata.copy(),
#                                 id_=f"{hash(file_path)}_{hash(chunk)}_{idx}"
#                             )
#                             documents.append(document)
#                 else:
#                     # 其他文件类型使用SimpleDirectoryReader处理
#                     reader = SimpleDirectoryReader(input_files=[file_path])
#                     docs = reader.load_data()
#                     for doc in docs:
#                         # 添加元数据
#                         doc.metadata.update({
#                             'db_name': db_name,
#                             'category': label,
#                             'data_type': 'unstructured'
#                         })
#                         # 分块处理
#                         nodes = node_parser.get_nodes_from_documents([doc])
#                         for node in nodes:
#                             # 智能分割超长内容
#                             safe_chunks = safe_split_content(node.text)
                            
#                             for idx, safe_chunk in enumerate(safe_chunks):
#                                 document = Document(
#                                     text=safe_chunk,
#                                     metadata=node.metadata.copy(),
#                                     id_=f"{node.id_}_{idx}"
#                                 )
#                                 documents.append(document)
#             except Exception as e:
#                 print(f"处理文件 {file_path} 时出错: {str(e)}")
#                 continue
    
#     # 分批创建索引（每批最多100个节点）
#     index = None
#     batch_size = 100
#     for i in range(0, len(documents), batch_size):
#         batch = documents[i:i+batch_size]
#         if index is None:
#             index = VectorStoreIndex(batch)
#         else:
#             for document in batch:
#                 index.insert(document)
    
#     # 保存索引
#     if index:
#         db_path = os.path.join(BASE_PATH, db_name)
#         os.makedirs(db_path, exist_ok=True)
#         index.storage_context.persist(db_path)
#         print(f"知识库 {db_name} 创建成功")
#     else:
#         print("没有可处理的文档内容")

# def create_structured_db(db_name: str, data_table: list):
#     """创建结构化知识库索引（完整保留内容）"""
#     print(f"知识库名称为：{db_name}，数据表名称为：{data_table}")
    
#     # 验证输入
#     if not data_table:
#         print("没有选择数据表")
#         return
#     elif len(db_name) == 0:
#         print("没有命名知识库")
#         return
#     elif db_name in os.listdir(BASE_PATH):
#         print("知识库已存在，请换个名字或删除原来知识库再创建")
#         return
    
#     nodes = []
#     for table in data_table:
#         table_path = os.path.join(CATEGORY_PATH, table)
#         if not os.path.exists(table_path):
#             continue
            
#         # 加载文档
#         reader = SimpleDirectoryReader(table_path)
#         docs = reader.load_data()
        
#         for doc in docs:
#             category = os.path.basename(table_path)
#             file_name = doc.metadata.get('file_name', '')
            
#             # 处理文档内容（按行分块）
#             doc_content = doc.get_content().split('\n')
#             for line_idx, chunk in enumerate(doc_content):
#                 if chunk.strip():
#                     # 智能分割超长行
#                     safe_chunks = safe_split_content(chunk)
                    
#                     for chunk_idx, safe_chunk in enumerate(safe_chunks):
#                         node = TextNode(text=safe_chunk)
#                         node.metadata = {
#                             'db_name': db_name,
#                             'category': category,
#                             'file_name': file_name,
#                             'file_path': doc.metadata.get('file_path', ''),
#                             'data_type': 'structured'
#                         }
#                         # 将 TextNode 转换为 Document
#                         document = Document(
#                             text=node.text,
#                             metadata=node.metadata,
#                             id_=f"{hash(doc.metadata.get('file_path', ''))}_{line_idx}_{chunk_idx}"
#                         )
#                         nodes.append(document)
    
#     # 分批创建索引
#     index = None
#     batch_size = 100
#     for i in range(0, len(nodes), batch_size):
#         batch = nodes[i:i+batch_size]
#         if index is None:
#             index = VectorStoreIndex(batch)
#         else:
#             for document in batch:
#                 index.insert(document)
    
#     # 保存索引
#     if index:
#         db_path = os.path.join(BASE_PATH, db_name)
#         os.makedirs(db_path, exist_ok=True)
#         index.storage_context.persist(db_path)
#         print(f"知识库 {db_name} 创建成功")
#     else:
#         print("没有可处理的文档内容")
