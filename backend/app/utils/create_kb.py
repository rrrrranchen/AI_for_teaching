from http import HTTPStatus
import os
import shutil
from fastapi import logger
from llama_index.core import VectorStoreIndex, Settings, SimpleDirectoryReader
from llama_index.embeddings.dashscope import (
    DashScopeEmbedding,
    DashScopeTextEmbeddingModels,
    DashScopeTextEmbeddingType,
)
from llama_index.core.schema import TextNode, Document
from llama_index.core.node_parser import SentenceSplitter

# 配置嵌入模型（添加批处理大小限制）
EMBED_MODEL = DashScopeEmbedding(
    model_name="text-embedding-v4",
    text_type=DashScopeTextEmbeddingType.TEXT_TYPE_DOCUMENT,
    embed_batch_size=8  # 设置为8，留出安全余量
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
    """创建非结构化知识库索引（带批处理限制）"""
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
        chunk_overlap=Settings.chunk_overlap
    )
    
    documents = []
    for label in label_name:
        label_path = os.path.join(CATEGORY_PATH, label)
        if not os.path.exists(label_path):
            continue
            
        # 分批加载文档
        reader = SimpleDirectoryReader(label_path)
        docs = reader.load_data()
        
        for doc in docs:
            # 添加元数据
            category = os.path.basename(label_path)
            doc.metadata.update({
                'db_name': db_name,
                'category': category,
                'data_type': 'unstructured'
            })
            
            # 分块处理
            nodes = node_parser.get_nodes_from_documents([doc])
            for node in nodes:
                # 将 TextNode 转换为 Document
                document = Document(
                    text=node.text,
                    metadata=node.metadata,
                    id_=node.id_  # 如果 TextNode 有 id_ 属性，否则可以省略
                )
                documents.append(document)
    
    # 分批创建索引（每批最多50个节点）
    index = None
    batch_size = 50
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
    batch_size = 50
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




import os
import shutil
from openai import OpenAI
from llama_index.core import StorageContext, load_index_from_storage
from typing import Generator, List, Tuple, Optional, Dict, Any
import dashscope  # 新增导入

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATEGORY_PATH = os.path.join(project_root, 'static', 'knowledge', 'category')
BASE_PATH = os.path.join(project_root, 'static', 'knowledge', 'base')

def _retrieve_chunks_from_multiple_dbs(
    query: str,
    db_names: List[str],
    similarity_threshold: float,
    chunk_cnt: int,
    data_type_filter: Optional[str] = None
) -> Tuple[str, str, Dict]:
    """
    从多个知识库检索相关文本块（支持混合类型）
    返回: (模型提示文本, 显示文本, 来源字典)
    """
    try:
        # 设置API Key（建议使用环境变量）
        dashscope.api_key = "sk-48f34d4f9c6948cbaa5198ab455f1224"
        
        all_nodes = []
        
        # 从所有知识库中检索节点
        for db_name in db_names:
            try:
                storage_context = StorageContext.from_defaults(
                    persist_dir=os.path.join(BASE_PATH, db_name)
                )
                index = load_index_from_storage(storage_context)
                retriever_engine = index.as_retriever(similarity_top_k=20)
                
                # 获取相关文本块
                retrieve_chunk = retriever_engine.retrieve(query)
                
                # 为每个节点添加知识库名称
                for node in retrieve_chunk:
                    if "db_name" not in node.metadata:
                        node.metadata["db_name"] = db_name
                all_nodes.extend(retrieve_chunk)
            except Exception as e:
                logger.error(f"加载知识库 {db_name} 失败: {str(e)}")
        
        # 如果没有检索到任何节点
        if not all_nodes:
            logger.warning("未检索到任何节点")
            return "", "", {}
        
        # 过滤并准备文档用于重排序
        valid_nodes = []
        documents = []
        
        for i, node in enumerate(all_nodes):
            # 检查文档是否为空或无效
            if not node.text or not node.text.strip():
                logger.warning(f"跳过空文档节点 (索引: {i}, 知识库: {node.metadata.get('db_name', '未知')})")
                continue
                
           
            
            
            valid_nodes.append(node)
            documents.append(node.text)
        
        # 检查文档数量限制
        if len(documents) > 500:
            logger.warning(f"文档数量超过500限制，仅取前500个 (总数: {len(documents)})")
            valid_nodes = valid_nodes[:500]
            documents = documents[:500]
        
        # 如果没有有效文档
        if not documents:
            logger.warning("无有效文档可供重排序")
            return "", "", {}
        
        # 调用gte-rerank-v2模型进行重排序
        try:
            resp = dashscope.TextReRank.call(
                model="gte-rerank-v2",
                query=query,
                documents=documents,
                top_n=min(chunk_cnt, len(documents)),  # 确保不超过可用文档数
                return_documents=True
            )
            
            if resp.status_code == HTTPStatus.OK:
                reranked_results = resp.output['results']
                
                # 创建映射：重排序索引 → 原始节点
                sorted_nodes = []
                for result in reranked_results:
                    # 获取原始索引位置
                    orig_index = result['index']
                    
                    # 验证索引范围
                    if 0 <= orig_index < len(valid_nodes):
                        node = valid_nodes[orig_index]
                        # 更新节点分数为新的相关性分数
                        node.score = result['relevance_score']
                        sorted_nodes.append(node)
                    else:
                        logger.error(f"无效索引: {orig_index} (最大索引: {len(valid_nodes)-1})")
                
                results = sorted_nodes
            else:
                logger.error(f"重排序API错误: {resp.code} - {resp.message}")
                logger.info("使用原始排序")
                valid_nodes.sort(key=lambda x: x.score, reverse=True)
                results = valid_nodes[:chunk_cnt]
                
        except Exception as e:
            logger.error(f"重排序失败: {str(e)}")
            valid_nodes.sort(key=lambda x: x.score, reverse=True)
            results = valid_nodes[:chunk_cnt]
        
        # 构建模型提示文本
        model_context = ""
        # 构建用于显示的召回文本
        display_context = ""
        # 构建来源字典 {db_name: {category: {file_name: [chunk_info]}}}
        source_dict = {}
        
        for i, result in enumerate(results):
            if result.score >= similarity_threshold:
                # 获取元数据
                metadata = result.metadata
                db_source = metadata.get("db_name", "未知知识库")
                category = metadata.get("category", "未知类目")
                file_name = metadata.get("file_name", "未知文件")
                data_type = metadata.get("data_type", "未知类型")
                
                # 添加到来源字典
                if db_source not in source_dict:
                    source_dict[db_source] = {}
                if category not in source_dict[db_source]:
                    source_dict[db_source][category] = {}
                if file_name not in source_dict[db_source][category]:
                    source_dict[db_source][category][file_name] = []
                
                chunk_info = {
                    "text": result.text,
                    "score": round(result.score, 2),
                    "position": i+1
                }
                source_dict[db_source][category][file_name].append(chunk_info)
                
                # 添加数据类型标记
                model_context += f"## {i+1} (来自: {db_source}/{category}/{file_name}, 类型: {data_type}):\n{result.text}\n\n"
                display_context += (
                    f"## 片段 {i+1} [评分: {round(result.score, 2)}]\n"
                    f"知识库: {db_source}\n"
                    f"类目: {category}\n"
                    f"文件: {file_name}\n"
                    f"内容: {result.text}\n\n"
                )
        
        return model_context, display_context, source_dict
    except Exception as e:
        logger.exception("知识库检索异常")
        return "", "", {}


def _get_model_config(model: str, thinking_mode: bool) -> Dict[str, Any]:
    """获取模型配置"""
    if thinking_mode:
        # 思考模式强制使用DeepSeek-Reasoner
        return {
            "model": "deepseek-reasoner",
            "base_url": "https://api.deepseek.com",
            "api_key": "sk-ca9d2a314fda4f8983f61e292a858d17",
            "system_prompt": "你是一个有帮助的助手，请根据提供的参考内容回答问题。",
            "is_reasoner": True
        }
    else:
        # 非思考模式使用用户选择的模型
        if "deepseek" in model.lower():
            return {
                "model": model,
                "base_url": "https://api.deepseek.com",
                "api_key": "sk-ca9d2a314fda4f8983f61e292a858d17",
                "system_prompt": "你是一个有帮助的助手，请根据提供的参考内容回答问题。",
                "is_reasoner": False
            }
        else:
            return {
                "model": model,
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "sk-48f34d4f9c6948cbaa5198ab455f1224",
                "system_prompt": "你是一个有帮助的助手，请根据提供的参考内容回答问题。",
                "is_reasoner": False
            }

def chat_stream(
    query: str,
    db_names: List[str] = ["default"],
    model: str = "qwen-max",
    temperature: float = 0.85,
    max_tokens: int = 4068,
    history: Optional[List[dict]] = None,
    similarity_threshold: float = 0.2,
    chunk_cnt: int = 5,
    api_key: Optional[str] = None,
    thinking_mode: bool = False,
    data_type_filter: Optional[str] = None
) -> Generator[Tuple[str, str, str, Optional[dict]], None, None]:
    """
    流式RAG聊天，支持来源追踪
    返回: 生成器 (token, chunks, status, source_dict)
    """
    # 获取模型配置
    config = _get_model_config(model, thinking_mode)
    
    # 优先使用传入的API密钥
    if api_key:
        config["api_key"] = api_key
        
    # 初始化OpenAI客户端
    client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    
    # 从多个知识库检索相关内容
    model_context, display_chunks, source_dict = _retrieve_chunks_from_multiple_dbs(
        query, db_names, similarity_threshold, chunk_cnt, data_type_filter
    )
    
    # 返回召回文本和来源字典
    yield "", display_chunks, "chunks", source_dict
    
    # 构建提示
    if model_context:
        prompt_template = f"请参考以下内容：\n{model_context}\n用户问题：{query}"
    else:
        prompt_template = query
    
    # 构建消息历史
    messages = [{"role": "system", "content": config["system_prompt"]}]
    
    # 添加对话历史
    if history:
        for msg in history[-5:]:  # 只保留最近的5条历史
            messages.append(msg)
    
    messages.append({"role": "user", "content": prompt_template})
    
    # 流式调用模型
    try:
        reasoning_content = ""
        final_content = ""
        
        # 对于Reasoner模型，需要特殊处理
        if config["is_reasoner"]:
            stream = client.chat.completions.create(
                model=config["model"],
                messages=messages,
                max_tokens=max_tokens,
                stream=True
            )
            
            # 处理Reasoner的流式响应
            for chunk in stream:
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # 处理思维链内容
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    token = delta.reasoning_content
                    reasoning_content += token
                    yield token, "", "reasoning", source_dict
                
                # 处理最终回答内容
                if hasattr(delta, 'content') and delta.content:
                    token = delta.content
                    final_content += token
                    yield token, "", "content", source_dict
            
            # 返回完整响应
            yield reasoning_content + final_content, "", "end", source_dict
            
        else:
            # 普通模型的流式响应处理
            stream = client.chat.completions.create(
                model=config["model"],
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    yield token, "", "tokens", source_dict
            
            # 返回完整响应和来源字典
            yield full_response, "", "end", source_dict
        
    except Exception as e:
        error_msg = f"⚠️ 模型调用失败: {str(e)}"
        yield error_msg, "", "error", source_dict

def format_sources(source_dict: Dict) -> str:
    """格式化来源信息为可读字符串"""
    if not source_dict:
        return "本次回答未引用特定来源"
    
    sources = []
    for db, categories in source_dict.items():
        for category, files in categories.items():
            for file, chunks in files.items():
                # 提取所有引用的片段位置
                chunk_positions = [str(c['position']) for c in chunks]
                chunk_refs = ", ".join(chunk_positions)
                
                # 提取代表性文本（第一个片段）
                representative_text = chunks[0]['text']
                if len(representative_text) > 100:
                    representative_text = representative_text[:100] + "..."
                
                sources.append(
                    f"知识库: {db}\n"
                    f"├─ 类目: {category}\n"
                    f"├─ 文件: {file}\n"
                    f"└─ 引用片段: {chunk_refs}\n"
                    f"   示例内容: {representative_text}"
                )
    
    return "\n\n".join([
        "本次回答参考了以下来源：",
        *sources
    ])


def main():
    # 测试对话参数
    query = " TensorFlow Lite发展历史"
    db_names = ["389e58c2-4f8c-4269-acf5-bd418b6e34f9_嵌入式开发"]
    model = "deepseek-reasoner"
    thinking_mode=True
    print(f"用户提问: {query}\n")
    print("="*50 + " 开始对话 " + "="*50)
    
    full_response = ""
    reasoning_content = ""
    
    # 调用 chat_stream 函数
    for token, chunks, status, source_dict in chat_stream(query, db_names, model, thinking_mode=thinking_mode):
        if status == "chunks":
            print("\n[召回的知识片段]:")
            print(chunks)
        elif status == "reasoning":
            reasoning_content += token
            print(token, end="", flush=True)  # 流式打印思维链
        elif status == "content":
            full_response += token
            print(token, end="", flush=True)  # 流式打印回答内容
        elif status == "tokens":
            full_response += token
            print(token, end="", flush=True)  # 普通模型的流式输出
        elif status == "end":
            if token:  # 如果是reasoner模型，这里会包含完整响应
                full_response = token
            print("\n\n[完整回答]:")
            print(full_response)
        elif status == "error":
            print(f"\n[错误]: {token}")
    
    # 格式化来源信息
    formatted_sources = format_sources(source_dict)
    print("\n" + "="*50 + " 来源信息 " + "="*50)
    print(formatted_sources)

if __name__ == "__main__":
    main()
