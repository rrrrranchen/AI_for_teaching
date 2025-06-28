import os
import shutil
import pandas as pd
from openai import OpenAI
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings
from llama_index.core.schema import TextNode
from llama_index.core import SimpleDirectoryReader
from llama_index.embeddings.dashscope import (
    DashScopeEmbedding,
    DashScopeTextEmbeddingModels,
    DashScopeTextEmbeddingType,
)
from llama_index.postprocessor.dashscope_rerank import DashScopeRerank
from typing import Generator, List, Tuple, Optional, Dict, Any
import json

# 配置常量
STRUCTURED_FILE_PATH = "backend/app/local_rag/File/Structured"
UNSTRUCTURED_FILE_PATH = "backend/app/local_rag/File/Unstructured"
DB_PATH = "backend/app/local_rag/VectorStore"
TMP_NAME = "backend/app/local_rag/tmp_abcd"

# 设置嵌入模型
EMBED_MODEL = DashScopeEmbedding(
    model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V2,
    text_type=DashScopeTextEmbeddingType.TEXT_TYPE_DOCUMENT,
)
Settings.embed_model = EMBED_MODEL

class RAGSystem:
    def __init__(self):
        # 确保目录存在
        os.makedirs(STRUCTURED_FILE_PATH, exist_ok=True)
        os.makedirs(UNSTRUCTURED_FILE_PATH, exist_ok=True)
        os.makedirs(DB_PATH, exist_ok=True)
    
    # ================= 文件管理功能 =================
    
    def list_unstructured_labels(self) -> List[str]:
        """获取所有非结构化数据类目"""
        return os.listdir(UNSTRUCTURED_FILE_PATH)
    
    def list_structured_tables(self) -> List[str]:
        """获取所有结构化数据表"""
        return os.listdir(STRUCTURED_FILE_PATH)
    
    def list_knowledge_bases(self) -> List[str]:
        """获取所有知识库"""
        return os.listdir(DB_PATH)
    
    def upload_unstructured_file(self, file_paths: List[str], label_name: str) -> str:
        """
        上传非结构化文件到指定类目
        :param file_paths: 文件路径列表
        :param label_name: 类目名称
        :return: 操作结果消息
        """
        if not file_paths:
            return "请上传文件"
        if not label_name:
            return "请输入类目名称"
        if label_name in self.list_unstructured_labels():
            return f"{label_name}类目已存在"
        
        try:
            label_path = os.path.join(UNSTRUCTURED_FILE_PATH, label_name)
            os.makedirs(label_path, exist_ok=True)
            
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                shutil.copy(file_path, os.path.join(label_path, file_name))
            
            return f"文件已上传至{label_name}类目中"
        except Exception as e:
            return f"上传失败: {str(e)}"
    
    def upload_structured_file(self, file_paths: List[str], table_name: str) -> str:
        """
        上传结构化文件并转换为文本格式
        :param file_paths: 文件路径列表
        :param table_name: 数据表名称
        :return: 操作结果消息
        """
        if not file_paths:
            return "请上传文件"
        if not table_name:
            return "请输入数据表名称"
        if table_name in self.list_structured_tables():
            return f"{table_name}数据表已存在"
        
        try:
            table_path = os.path.join(STRUCTURED_FILE_PATH, table_name)
            os.makedirs(table_path, exist_ok=True)
            
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(table_path, file_name)
                shutil.copy(file_path, dest_path)
                
                # 转换结构化数据为文本
                if file_name.endswith(".xlsx"):
                    df = pd.read_excel(dest_path)
                elif file_name.endswith(".csv"):
                    df = pd.read_csv(dest_path)
                else:
                    continue
                
                txt_file_name = os.path.splitext(file_name)[0] + '.txt'
                with open(os.path.join(table_path, txt_file_name), "w") as f:
                    for idx, row in df.iterrows():
                        info = [f"{col}:{row[col]}" for col in df.columns]
                        f.write("【" + ",".join(info) + "】\n")
                
                os.remove(dest_path)
            
            return f"文件已上传至{table_name}数据表中"
        except Exception as e:
            return f"上传失败: {str(e)}"
    
    def delete_label(self, label_name: str) -> str:
        """删除非结构化数据类目"""
        if not label_name:
            return "请选择类目"
        
        label_path = os.path.join(UNSTRUCTURED_FILE_PATH, label_name)
        if os.path.exists(label_path):
            shutil.rmtree(label_path)
            return f"{label_name}类目已删除"
        return f"{label_name}类目不存在"
    
    def delete_table(self, table_name: str) -> str:
        """删除结构化数据表"""
        if not table_name:
            return "请选择数据表"
        
        table_path = os.path.join(STRUCTURED_FILE_PATH, table_name)
        if os.path.exists(table_path):
            shutil.rmtree(table_path)
            return f"{table_name}数据表已删除"
        return f"{table_name}数据表不存在"
    
    # ================= 知识库管理功能 =================
    
    def create_unstructured_db(self, db_name: str, label_names: List[str]) -> str:
        """
        从非结构化数据创建知识库
        :param db_name: 知识库名称
        :param label_names: 类目名称列表
        :return: 操作结果消息
        """
        if not label_names:
            return "没有选择类目"
        if not db_name:
            return "没有命名知识库"
        if db_name in self.list_knowledge_bases():
            return "知识库已存在，请换个名字"
        
        try:
            documents = []
            for label in label_names:
                label_path = os.path.join(UNSTRUCTURED_FILE_PATH, label)
                documents.extend(SimpleDirectoryReader(label_path).load_data())
            
            index = VectorStoreIndex.from_documents(documents)
            db_path = os.path.join(DB_PATH, db_name)
            os.makedirs(db_path, exist_ok=True)
            index.storage_context.persist(db_path)
            
            return "知识库创建成功"
        except Exception as e:
            return f"知识库创建失败: {str(e)}"
    
    def create_structured_db(self, db_name: str, table_names: List[str]) -> str:
        """
        从结构化数据创建知识库
        :param db_name: 知识库名称
        :param table_names: 数据表名称列表
        :return: 操作结果消息
        """
        if not table_names:
            return "没有选择数据表"
        if not db_name:
            return "没有命名知识库"
        if db_name in self.list_knowledge_bases():
            return "知识库已存在，请换个名字"
        
        try:
            documents = []
            for table in table_names:
                table_path = os.path.join(STRUCTURED_FILE_PATH, table)
                documents.extend(SimpleDirectoryReader(table_path).load_data())
            
            nodes = []
            for doc in documents:
                doc_content = doc.get_content().split('\n')
                for chunk in doc_content:
                    node = TextNode(text=chunk)
                    node.metadata = {
                        'source': doc.get_doc_id(),
                        'file_name': doc.metadata['file_name']
                    }
                    nodes.append(node)
            
            index = VectorStoreIndex(nodes)
            db_path = os.path.join(DB_PATH, db_name)
            os.makedirs(db_path, exist_ok=True)
            index.storage_context.persist(db_path)
            
            return "知识库创建成功"
        except Exception as e:
            return f"知识库创建失败: {str(e)}"
    
    def delete_knowledge_base(self, db_name: str) -> str:
        """删除知识库"""
        if not db_name:
            return "请选择知识库"
        
        db_path = os.path.join(DB_PATH, db_name)
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
            return f"已成功删除{db_name}知识库"
        return f"{db_name}知识库不存在"
    
    # ================= RAG聊天功能 =================
    
    def _retrieve_chunks(self, query: str, db_name: str, similarity_threshold: float, chunk_cnt: int) -> Tuple[str, str]:
        """
        从知识库检索相关文本块
        :param query: 查询文本
        :param db_name: 知识库名称
        :param similarity_threshold: 相似度阈值
        :param chunk_cnt: 返回的文本块数量
        :return: (用于模型提示的文本, 用于显示的召回文本)
        """
        try:
            dashscope_rerank = DashScopeRerank(top_n=chunk_cnt, return_documents=True)
            storage_context = StorageContext.from_defaults(
                persist_dir=os.path.join(DB_PATH, db_name)
            )
            index = load_index_from_storage(storage_context)
            retriever_engine = index.as_retriever(similarity_top_k=20)
            
            # 获取相关文本块
            retrieve_chunk = retriever_engine.retrieve(query)
            try:
                results = dashscope_rerank.postprocess_nodes(retrieve_chunk, query_str=query)
            except Exception:
                results = retrieve_chunk[:chunk_cnt]
            
            # 构建模型提示文本
            model_context = ""
            # 构建用于显示的召回文本
            display_context = ""
            
            for i, result in enumerate(results):
                if result.score >= similarity_threshold:
                    model_context += f"## {i+1}:\n{result.text}\n\n"
                    display_context += f"## {i+1}:\n{result.text}\nscore: {round(result.score, 2)}\n\n"
            
            return model_context, display_context
        except Exception as e:
            print(f"知识库检索异常: {str(e)}")
            return "", ""
    
    def _get_model_config(self, model: str, thinking_mode: bool) -> Dict[str, Any]:
        """获取模型配置"""
        if thinking_mode:
            # 思考模式强制使用DeepSeek-Reasoner
            return {
                "model": "deepseek-reasoner",
                "base_url": "https://api.deepseek.com",
                "api_key": "sk-b7550aa67ed840ffacb5ca051733802c",
                "system_prompt": "你是一个有帮助的助手，请根据提供的参考内容回答问题。",
                "is_reasoner": True
            }
        else:
            # 非思考模式使用用户选择的模型
            if "deepseek" in model.lower():
                return {
                    "model": model,
                    "base_url": "https://api.deepseek.com",
                    "api_key": "sk-b7550aa67ed840ffacb5ca051733802c",
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
        self,
        query: str,
        db_name: str = "default",
        model: str = "qwen-max",
        temperature: float = 0.85,
        max_tokens: int = 4068,
        history: Optional[List[dict]] = None,
        similarity_threshold: float = 0.2,
        chunk_cnt: int = 5,
        api_key: Optional[str] = None,
        thinking_mode: bool = False
    ) -> Generator[Tuple[str, str, str], None, None]:
        """
        流式RAG聊天，支持DeepSeek-Reasoner思维链
        :param query: 用户查询
        :param db_name: 知识库名称
        :param model: 模型名称
        :param temperature: 温度参数
        :param max_tokens: 最大token数
        :param history: 对话历史
        :param similarity_threshold: 相似度阈值
        :param chunk_cnt: 召回片段数
        :param api_key: API密钥
        :param thinking_mode: 是否启用思考模式（流式输出思维链）
        :return: 生成器，产生 (token, chunks, status)
                 其中 status: 'chunks'表示召回文本, 
                       'reasoning'表示思维链内容,
                       'content'表示最终回答,
                       'end'表示结束
        """
        # 获取模型配置
        config = self._get_model_config(model, thinking_mode)
        
        # 优先使用传入的API密钥
        if api_key:
            config["api_key"] = api_key
            
        # 初始化OpenAI客户端
        client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
        
        # 从知识库检索相关内容
        model_context, display_chunks = self._retrieve_chunks(
            query, db_name, similarity_threshold, chunk_cnt
        )
        
        # 返回召回文本
        yield "", display_chunks, "chunks"
        
        # 构建提示
        if model_context:
            prompt_template = f"请参考以下内容：\n{model_context}\n用户问题：{query}"
        else:
            prompt_template = query
        
        # 构建消息历史
        messages = [{"role": "system", "content": config["system_prompt"]}]
        
        # 添加对话历史（只包含最终回答，不包含思维链）
        if history:
            for msg in history[-5:]:  # 只保留最近的5条历史
                # 确保历史消息中不包含思维链内容
                if "reasoning_content" not in msg:
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
                        yield token, "", "reasoning"
                    
                    # 处理最终回答内容
                    if hasattr(delta, 'content') and delta.content:
                        token = delta.content
                        final_content += token
                        yield token, "", "content"
                
                # 返回完整响应
                yield reasoning_content + final_content, "", "end"
                
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
                        yield token, "", "tokens"
                
                # 返回完整响应
                yield full_response, "", "end"
            
        except Exception as e:
            error_msg = f"⚠️ 模型调用失败: {str(e)}"
            yield error_msg, "", "error"

# 使用示例
if __name__ == "__main__":
    rag = RAGSystem()

# 思考模式（DeepSeek-Reasoner）
    for token, chunks, status in rag.chat_stream(
        "适配器模式是什么？",db_name="设计模式",model="deepseek-reasoner",
        thinking_mode=True
    ):
        if status == "chunks":
            print("召回内容:", chunks)
        elif status == "reasoning":
            print(token, end="", flush=True)
        elif status == "content":
            print(token, end="", flush=True)
        elif status == "end":
            print("\n回答完成")
    