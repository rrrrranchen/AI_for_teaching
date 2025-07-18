from http import HTTPStatus
import os
import shutil
from venv import logger

from llama_cloud import MetadataFilter, MetadataFilters
from openai import OpenAI
from llama_index.core import StorageContext, load_index_from_storage
from typing import Generator, List, Tuple, Optional, Dict, Any
from app.config import Config
import dashscope  

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
        
        dashscope.api_key = Config.DASHSCOPE_API_KEY
        
        all_nodes = []
        
        # 从所有知识库中检索节点
        for db_name in db_names:
            try:
                storage_context = StorageContext.from_defaults(
                    persist_dir=os.path.join(BASE_PATH, db_name)
                )
                index = load_index_from_storage(storage_context)
                # 增加检索数量以捕获更多相关片段
                retriever_engine = index.as_retriever(similarity_top_k=50)  # 从20增加到50
                
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
                
            # 如果指定了数据类型过滤器，进行过滤
            if data_type_filter and node.metadata.get("data_type") != data_type_filter:
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
                top_n=min(50, len(documents)),  # 增加重排序数量到50
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
                results = valid_nodes[:min(50, len(valid_nodes))]  # 同样增加到50
                
        except Exception as e:
            logger.error(f"重排序失败: {str(e)}")
            valid_nodes.sort(key=lambda x: x.score, reverse=True)
            results = valid_nodes[:min(50, len(valid_nodes))]  # 同样增加到50
        
        # 关键优化：确保来自不同文件的片段被包含
        # 1. 按文件分组
        file_groups = {}
        for result in results:
            file_key = result.metadata.get("file_path", "unknown")
            if file_key not in file_groups:
                file_groups[file_key] = []
            file_groups[file_key].append(result)
        
        # 2. 每个文件取前N个片段 (N=5)
        top_results = []
        for file, file_results in file_groups.items():
            sorted_file_results = sorted(file_results, key=lambda x: x.score, reverse=True)[:5]
            top_results.extend(sorted_file_results)
        
        # 3. 所有片段按分数排序
        final_results = sorted(top_results, key=lambda x: x.score, reverse=True)[:chunk_cnt]
        
        # 构建模型提示文本
        model_context = ""
        # 构建用于显示的召回文本
        display_context = ""
        # 构建来源字典 {db_name: {category: {file_name: [chunk_info]}}}
        source_dict = {}
        
        for i, result in enumerate(final_results):
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


def _retrieve_chunks_from_multiple_dbs_for_questions(
    query: str,
    db_names: List[str],
    similarity_threshold: float,
    chunk_cnt: int,
    data_type_filter: Optional[str] = None
) -> Tuple[str, str, Dict]:
    """
    修复版知识库检索函数：
    1. 解决元数据过滤API调用问题
    2. 增强错误处理和日志记录
    """
    try:
        dashscope.api_key = Config.DASHSCOPE_API_KEY
        all_nodes = []
        question_bank_nodes = []  # 确保变量初始化
        
        # 从所有知识库中检索节点
        for db_name in db_names:
            try:
                storage_context = StorageContext.from_defaults(
                    persist_dir=os.path.join(BASE_PATH, db_name)
                )
                index = load_index_from_storage(storage_context)
                retriever = index.as_retriever(similarity_top_k=50)
                
                # 初始化当前知识库的节点列表
                current_question_bank_nodes = []
                current_other_nodes = []
                
                # 尝试优先检索题库类型
                try:
                    # 修复元数据过滤调用方式
                    retrieved_nodes = retriever.retrieve(query)
                    
                    # 手动筛选题库节点
                    for node in retrieved_nodes:
                        if node.metadata.get("data_type") == "question_bank":
                            current_question_bank_nodes.append(node)
                        else:
                            current_other_nodes.append(node)
                    logger.info(f"找到 {len(current_question_bank_nodes)} 个题库节点")
                    
                except Exception as e:
                    # 元数据过滤失败时的回退方案
                    logger.warning(f"元数据过滤失败: {str(e)}")
                    retrieved_nodes = retriever.retrieve(query)
                    
                    # 手动筛选题库节点
                    for node in retrieved_nodes:
                        if node.metadata.get("data_type") == "question_bank":
                            current_question_bank_nodes.append(node)
                        else:
                            current_other_nodes.append(node)
                    logger.info(f"回退检索: 找到 {len(current_question_bank_nodes)} 个题库节点")
                
                # 添加知识库名称到元数据
                for node in current_question_bank_nodes:
                    node.metadata.setdefault("db_name", db_name)
                for node in current_other_nodes:
                    node.metadata.setdefault("db_name", db_name)
                
                # 将节点添加到总列表
                all_nodes.extend(current_question_bank_nodes)
                
                # 如果题库节点不足，补充其他类型节点
                if len(current_question_bank_nodes) < 30 and current_other_nodes:
                    # 按分数排序后取最相关的
                    current_other_nodes.sort(key=lambda x: x.score, reverse=True)
                    all_nodes.extend(current_other_nodes[:50 - len(current_question_bank_nodes)])
                
                # 更新全局题库节点列表
                question_bank_nodes.extend(current_question_bank_nodes)
                
            except Exception as e:
                logger.error(f"加载知识库 {db_name} 失败: {str(e)}")
                continue
        
        # 如果没有检索到任何节点
        if not all_nodes:
            logger.warning("未检索到任何节点")
            return "", "", {}
        
        # 分离题库节点和其他节点（如果未完成）
        if not question_bank_nodes:
            question_bank_nodes = [n for n in all_nodes if n.metadata.get("data_type") == "question_bank"]
            other_nodes = [n for n in all_nodes if n.metadata.get("data_type") != "question_bank"]
        else:
            other_nodes = [n for n in all_nodes if n not in question_bank_nodes]
        
        # 优先使用题库节点，不足时补充其他节点
        if question_bank_nodes:
            logger.info(f"共找到 {len(question_bank_nodes)} 个题库节点")
            candidate_nodes = question_bank_nodes
            if len(question_bank_nodes) < 50 and other_nodes:
                # 按分数排序后补充其他节点
                other_nodes.sort(key=lambda x: x.score, reverse=True)
                candidate_nodes.extend(other_nodes[:50 - len(question_bank_nodes)])
        else:
            candidate_nodes = all_nodes
        
        # 准备文档用于重排序
        valid_nodes = candidate_nodes[:500]  # 限制数量
        documents = [node.text for node in valid_nodes]
        
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
                top_n=min(50, len(documents)),
                return_documents=True
            )
            
            if resp.status_code == HTTPStatus.OK:
                reranked_results = resp.output['results']
                
                # 创建映射：重排序索引 → 原始节点
                sorted_nodes = []
                for result in reranked_results:
                    orig_index = result['index']
                    if 0 <= orig_index < len(valid_nodes):
                        node = valid_nodes[orig_index]
                        node.score = result['relevance_score']  # 更新分数
                        sorted_nodes.append(node)
                
                results = sorted_nodes
            else:
                logger.error(f"重排序API错误: {resp.code} - {resp.message}")
                logger.info("使用原始排序")
                valid_nodes.sort(key=lambda x: x.score, reverse=True)
                results = valid_nodes[:min(50, len(valid_nodes))]
                
        except Exception as e:
            logger.error(f"重排序失败: {str(e)}")
            valid_nodes.sort(key=lambda x: x.score, reverse=True)
            results = valid_nodes[:min(50, len(valid_nodes))]
        
        # 直接取分数最高的结果
        final_results = sorted(results, key=lambda x: x.score, reverse=True)[:chunk_cnt]
        
        # 构建输出
        model_context = ""
        display_context = ""
        source_dict = {}
        
        for i, result in enumerate(final_results):
            if result.score >= similarity_threshold:
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
                
                # 构建上下文文本
                model_context += f"## {i+1} (来自: {db_source}/{category}/{file_name}, 类型: {data_type}):\n{result.text}\n\n"
                
                # 简化的显示文本
                display_context += (
                    f"## 题目 {i+1} [评分: {round(result.score, 2)}]\n"
                    f"来源: {file_name}\n"
                    f"内容: {result.text[:200]}...\n\n"
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
            "api_key": Config.DEEPSEEK_API_KEY,
            "system_prompt": """
            ## 定位
            你是一个专业的学习助手，专注于帮助学生高效学习、理解课程内容、解决学习难题，并促进知识掌握。目标是成为学生的支持伙伴，提供个性化教育指导。

            ## 能力
            - 清晰解释复杂概念，使用简单易懂的语言
            - 解答学科相关问题，提供分步解决方案
            - 生成定制练习题和复习材料
            - 建议学习策略、时间管理技巧和考试准备方法
            - 提供鼓励性反馈，引导学生独立思考

            ## 知识储备
            - 精通大学基础科目：高等数学、线性代数、概率论与数理统计、离散数学等学科，以及大学计算机相关科目：计算机网络、操作系统、计算机组成、软件架构等学科
            - 掌握学习心理学基础、记忆技巧和高效学习方法
            - 熟悉常见教材、课程大纲和教育标准

             ## 输出要求
            - 完整复现参考资料中的内容
            - 修复参考内容中的markdown格式
            - 回答内容需要完整覆盖参考资料中的所有相关内容
            
            """,
            "is_reasoner": True
        }
    else:
        # 非思考模式使用用户选择的模型
        if "deepseek" in model.lower():
            return {
                "model": model,
                "base_url": "https://api.deepseek.com",
                "api_key": Config.DEEPSEEK_API_KEY,
                "system_prompt": """
            ## 定位
            你是一个专业的学习助手，专注于帮助学生高效学习、理解课程内容、解决学习难题，并促进知识掌握。目标是成为学生的支持伙伴，提供个性化教育指导。

            ## 能力
            - 清晰解释复杂概念，使用简单易懂的语言
            - 解答学科相关问题，提供分步解决方案
            - 生成定制练习题和复习材料
            - 建议学习策略、时间管理技巧和考试准备方法
            - 提供鼓励性反馈，引导学生独立思考

            ## 知识储备
            - 精通大学基础科目：高等数学、线性代数、概率论与数理统计、离散数学等学科，以及大学计算机相关科目：计算机网络、操作系统、计算机组成、软件架构等学科
            - 掌握学习心理学基础、记忆技巧和高效学习方法
            - 熟悉常见教材、课程大纲和教育标准

             ## 输出要求
            - 完整复现参考资料中的内容
            - 修复参考内容中的markdown格式
            - 回答内容需要完整覆盖参考资料中的所有相关内容
            """,
                "is_reasoner": False
            }
        else:
            return {
                "model": model,
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": Config.DASHSCOPE_API_KEY,
                "system_prompt": """
            ## 定位
            你是一个专业的学习助手，专注于帮助学生高效学习、理解课程内容、解决学习难题，并促进知识掌握。目标是成为学生的支持伙伴，提供个性化教育指导。

            ## 能力
            - 清晰解释复杂概念，使用简单易懂的语言
            - 解答学科相关问题，提供分步解决方案
            - 生成定制练习题和复习材料
            - 建议学习策略、时间管理技巧和考试准备方法
            - 提供鼓励性反馈，引导学生独立思考

            ## 知识储备
            - 精通大学基础科目：高等数学、线性代数、概率论与数理统计、离散数学等学科，以及大学计算机相关科目：计算机网络、操作系统、计算机组成、软件架构等学科
            - 掌握学习心理学基础、记忆技巧和高效学习方法
            - 熟悉常见教材、课程大纲和教育标准

             ## 输出要求
            - 完整复现参考资料中的内容
            - 修复参考内容中的markdown格式
            - 回答内容需要完整覆盖参考资料中的所有相关内容
            """,
                "is_reasoner": False
            }


def _get_model_config2(model: str, thinking_mode: bool) -> Dict[str, Any]:
    """获取模型配置"""
    if thinking_mode:
        # 思考模式强制使用DeepSeek-Reasoner
        return {
            "model": "deepseek-reasoner",
            "base_url": "https://api.deepseek.com",
            "api_key": Config.DEEPSEEK_API_KEY,
            "system_prompt": """
            ## 定位
            你是一个专业的学习助手，专注于帮助学生高效学习、理解课程内容、解决学习难题，并促进知识掌握。目标是成为学生的支持伙伴，提供个性化教育指导。

            ## 回答方向
            - 不要直接告诉学生答案，逐步引导其走向最终答案
            - 态度要温和，从相关知识点中找到突破点

            """,
            "is_reasoner": True
        }
    else:
        # 非思考模式使用用户选择的模型
        if "deepseek" in model.lower():
            return {
                "model": model,
                "base_url": "https://api.deepseek.com",
                "api_key": Config.DEEPSEEK_API_KEY,
                "system_prompt": """
            ## 定位
            你是一个专业的学习助手，专注于帮助学生高效学习、理解课程内容、解决学习难题，并促进知识掌握。目标是成为学生的支持伙伴，提供个性化教育指导。

            ## 回答方向
            - 不要直接告诉学生答案，逐步引导其走向最终答案
            - 态度要温和，从相关知识点中找到突破点
           

            """,
                "is_reasoner": False
            }
        else:
            return {
                "model": model,
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": Config.DASHSCOPE_API_KEY,
                "system_prompt": """
            ## 定位
            你是一个专业的学习助手，专注于帮助学生高效学习、理解课程内容、解决学习难题，并促进知识掌握。目标是成为学生的支持伙伴，提供个性化教育指导。

            ## 回答方向
            - 不要直接告诉学生答案，逐步引导其走向最终答案
            - 态度要温和，从相关知识点中找到突破点

            """,
                "is_reasoner": False
            }



def chat_stream(
    query: str,
    db_names: List[str] = ["default"],
    model: str = "qwen-max",
    temperature: float = 0.85,
    max_tokens: int = 8000,
    history: Optional[List[dict]] = None,
    similarity_threshold: float = 0.2,
    chunk_cnt: int = 20,
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
    print(model_context)
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


def chat_stream2(
    query: str,
    db_names: List[str] = ["default"],
    model: str = "qwen-max",
    temperature: float = 0.85,
    max_tokens: int = 8000,
    history: Optional[List[dict]] = None,
    similarity_threshold: float = 0.2,
    chunk_cnt: int = 20,
    api_key: Optional[str] = None,
    thinking_mode: bool = False,
    data_type_filter: Optional[str] = None
) -> Generator[Tuple[str, str, str, Optional[dict]], None, None]:
    """
    流式RAG聊天，支持来源追踪
    返回: 生成器 (token, chunks, status, source_dict)
    """
    # 获取模型配置
    config = _get_model_config2(model, thinking_mode)
    
    # 优先使用传入的API密钥
    if api_key:
        config["api_key"] = api_key
        
    # 初始化OpenAI客户端
    client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    
    # 从多个知识库检索相关内容
    model_context, display_chunks, source_dict = _retrieve_chunks_from_multiple_dbs(
        query, db_names, similarity_threshold, chunk_cnt, data_type_filter
    )
    print(model_context)
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
    query = "请解释TensorFlow.js 的核心概念"
    db_names = ["2188a331-5352-4709-a07c-15ca92e9c752_tensor知识库"]
    model = "deepseek-chat"
    thinking_mode=True
    print(f"用户提问: {query}\n")
    print("="*50 + " 开始对话 " + "="*50)
    
    full_response = ""
    reasoning_content = ""
    
    # 调用 chat_stream 函数
    for token, chunks, status, source_dict in chat_stream(query, db_names, model):
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