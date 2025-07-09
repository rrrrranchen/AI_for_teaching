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
    """创建非结构化知识库索引（优化Markdown分块，确保接近3000字符）"""
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
    
    # 初始化文档处理器（chunk_size=3000）
    node_parser = SentenceSplitter(
        chunk_overlap=Settings.chunk_overlap,
        chunk_size=3000
    )
    
    def optimized_markdown_split(content: str) -> list[str]:
        """优化Markdown分块逻辑，确保分块接近3000字符"""
        chunks = []
        current_chunk = []
        current_length = 0
        
        # 按行处理
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped_line = line.strip()
            line_length = len(line)
            
            # 如果当前行是标题，尝试合并后续内容
            if stripped_line.startswith('#'):
                # 收集标题及后续内容直到达到块大小
                section_lines = []
                section_length = 0
                
                # 添加标题行
                section_lines.append(line)
                section_length += line_length
                
                # 添加后续内容直到达到3000字符或遇到下一个标题
                j = i + 1
                while j < len(lines) and section_length < 2500:  # 留500字符缓冲
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    
                    # 遇到新标题则停止
                    if next_stripped.startswith('#'):
                        break
                    
                    section_lines.append(next_line)
                    section_length += len(next_line)
                    j += 1
                
                # 如果收集到的内容足够大，直接作为独立块
                if section_length >= 500:  # 最小有效块大小
                    chunk_text = '\n'.join(section_lines)
                    chunks.append(chunk_text)
                    i = j  # 跳过已处理的行
                    continue
                else:
                    # 如果内容太小，添加到当前块
                    current_chunk.extend(section_lines)
                    current_length += section_length
                    i = j
                    continue
            
            # 普通行处理
            if current_length + line_length <= 3000:
                # 添加到当前块
                current_chunk.append(line)
                current_length += line_length
                i += 1
            else:
                # 当前块已接近3000字符，保存当前块
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:
                        chunks.append(chunk_text)
                
                # 开始新块（除非当前行特别长）
                if line_length > 3000:
                    # 处理超长行（如代码块）
                    chunks.append(line)
                    current_chunk = []
                    current_length = 0
                    i += 1
                else:
                    current_chunk = [line]
                    current_length = line_length
                    i += 1
        
        # 处理最后一个块
        if current_chunk:
            chunk_text = '\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)
        
        # 合并过小的块
        merged_chunks = []
        for chunk in chunks:
            if not merged_chunks or len(merged_chunks[-1]) + len(chunk) > 3000:
                # 开始新块
                merged_chunks.append(chunk)
            else:
                # 合并到前一个块
                merged_chunks[-1] += '\n\n' + chunk
        
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
                file_paths.append(os.path.join(root, file))
        
        for file_path in file_paths:
            # 获取文件扩展名
            file_ext = os.path.splitext(file_path)[1].lower()
            
            try:
                # 读取文件内容
                if file_ext == '.md':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
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
                        # 检查是否包含图片
                        if '![' in chunk or '<img' in chunk:
                            base_metadata['has_image'] = True
                        
                        document = Document(
                            text=chunk,
                            metadata=base_metadata.copy(),
                            id_=f"{hash(file_path)}_{hash(chunk)}"
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
                            'data_type': 'unstructured'
                        })
                        # 分块处理
                        nodes = node_parser.get_nodes_from_documents([doc])
                        for node in nodes:
                            document = Document(
                                text=node.text,
                                metadata=node.metadata,
                                id_=node.id_
                            )
                            documents.append(document)
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {str(e)}")
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
        print(f"知识库 {db_name} 创建成功")
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




