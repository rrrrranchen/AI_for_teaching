import os
import shutil
import pandas as pd
from openai import OpenAI
from llama_index.core import  StorageContext, load_index_from_storage
from llama_index.postprocessor.dashscope_rerank import DashScopeRerank
from typing import Generator, List, Tuple, Optional, Dict, Any

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
        dashscope_rerank = DashScopeRerank(top_n=chunk_cnt, return_documents=True)
        all_nodes = []
        
        # 从所有知识库中检索节点
        for db_name in db_names:
            storage_context = StorageContext.from_defaults(
                persist_dir=os.path.join(BASE_PATH, db_name)
            )
            index = load_index_from_storage(storage_context)
            retriever_engine = index.as_retriever(similarity_top_k=20)
            
            # 获取相关文本块
            retrieve_chunk = retriever_engine.retrieve(query)
            
            # 为每个节点添加知识库名称（如果元数据中不存在）
            for node in retrieve_chunk:
                if "db_name" not in node.metadata:
                    node.metadata["db_name"] = db_name
            all_nodes.extend(retrieve_chunk)
        
        # 如果没有检索到任何节点
        if not all_nodes:
            return "", "", {}
        
        # 对所有节点进行重排序
        try:
            results = dashscope_rerank.postprocess_nodes(all_nodes, query_str=query)
        except Exception as e:
            print(f"重排序失败，使用原始排序: {str(e)}")
            all_nodes.sort(key=lambda x: x.score, reverse=True)
            results = all_nodes[:chunk_cnt]
        
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
        print(f"知识库检索异常: {str(e)}")
        return "", "", {}

def _get_model_config(model: str, thinking_mode: bool) -> Dict[str, Any]:
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
    query = "请问陕北农村刘俊涛给出的分数是多少"
    db_names = ["0a37972c-bcbc-49ec-87ca-8ee612dba752_示例知识库", "8659491f-160b-48c3-967f-2a4d9ccce752_示例知识库"]
    model = "deepseek-reasoner"
    temperature = 0.85
    max_tokens = 4068
    history = []  
    similarity_threshold = 0.2
    chunk_cnt = 5
    thinking_mode = True
    data_type_filter = None

    for token, chunks, status, source_dict in chat_stream(
        query, db_names, model, temperature, max_tokens, history, similarity_threshold, chunk_cnt, thinking_mode, data_type_filter
    ):
        if status == "chunks":
            print("召回文本：")
            print(chunks)
        elif status == "reasoning":
            print("思维链：")
            print(token)
        elif status == "content":
            print("回答内容：")
            print(token)
        elif status == "end":
            print("完整回答：")
            print(token)
            print("来源信息：")
            print(format_sources(source_dict))
        elif status == "error":
            print("错误信息：")
            print(token)

# 运行主函数
if __name__ == "__main__":
    main()