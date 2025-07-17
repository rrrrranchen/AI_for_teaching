# app/services/knowledge_extractor.py
import hashlib
import os
import re
from django.conf import Settings
import requests
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Tuple, Dict
from collections import defaultdict
from http import HTTPStatus
import os
import re
import shutil
from typing import List
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
import os
from typing import List, Dict
from alibabacloud_nlp_automl20191111.client import Client as nlp_automl20191111Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_nlp_automl20191111 import models as nlp_automl_models
from alibabacloud_tea_util import models as util_models
from transformers import AutoModelForTokenClassification 
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
class KnowledgeExtractor:
    def __init__(self, domain: str = "general"):
        self.domain = domain
        self.ner_model = None
        self.ner_tokenizer = None
        self.relation_model = None
        self.relation_tokenizer = None
        
        # 领域特定配置
        self.domain_config = self._load_domain_config(domain)
        
        # 初始化模型
        self._init_models()

    def _load_domain_config(self, domain: str) -> dict:
        """加载领域特定配置"""
        config = {
            "general": {
                "ner_model": "D:\\download\\02chinese-bert",  # 您的本地路径
                "relation_labels": ["无关系", "属于", "包含", "相关", "影响", "依赖", "替代", "相似"]
            },
            # 其他领域配置...
        }
        return config.get(domain, config["general"])
    
    def _init_models(self):
        """初始化模型"""
        # 初始化NER模型
        try:
            ner_model_path = self.domain_config["ner_model"]
            self.ner_tokenizer = AutoTokenizer.from_pretrained(ner_model_path)
            self.ner_model = AutoModelForTokenClassification.from_pretrained(ner_model_path)
            self.ner_model.eval()
            if torch.cuda.is_available():
                self.ner_model.cuda()
            print(f"已加载 {self.domain} 领域NER模型: {ner_model_path}")
        except Exception as e:
            print(f"加载NER模型失败: {str(e)}")
            self.ner_model = None

    def extract_entities(self, text: str) -> List[dict]:
        """使用chinese-bert-base-ner提取实体"""
        if not self.ner_model or not text.strip():
            return []
        
        # 准备模型输入（不再使用offset_mapping）
        inputs = self.ner_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.ner_model(**inputs)
        
        predictions = torch.argmax(outputs.logits, dim=2)[0].cpu().numpy()
        tokens = self.ner_tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        
        # 解码实体
        entities = []
        current_entity = None
        
        for i, (token, pred) in enumerate(zip(tokens, predictions)):
            # 跳过特殊token
            if token in ["[CLS]", "[SEP]", "[PAD]"]:
                continue
                
            label = self.ner_model.config.id2label[pred]
            
            # 处理实体边界
            if label.startswith("B-"):
                if current_entity:
                    entities.append(current_entity)
                current_entity = {
                    "word": token.replace("##", ""),
                    "type": label[2:],  # 去掉B-前缀
                    "start": i,
                    "end": i+1
                }
            elif label.startswith("I-") and current_entity and current_entity["type"] == label[2:]:
                current_entity["word"] += token.replace("##", "")
                current_entity["end"] = i+1
            else:
                if current_entity:
                    entities.append(current_entity)
                current_entity = None
        
        # 转换token位置到字符位置
        char_positions = []
        pos = 0
        for token in tokens:
            if token in ["[CLS]", "[SEP]", "[PAD]"]:
                continue
            token = token.replace("##", "")
            char_positions.append((pos, pos + len(token)))
            pos += len(token) + 1  # +1 for space
        
        # 格式化输出
        formatted_entities = []
        for ent in entities:
            try:
                char_start = char_positions[ent["start"]][0]
                char_end = char_positions[ent["end"]-1][1]
                formatted_entities.append({
                    "word": ent["word"],
                    "type": ent["type"],
                    "offset": char_start,
                    "length": char_end - char_start
                })
            except IndexError:
                continue
        
        return formatted_entities
    
    def _extract_entities_from_domain_dict(self, text: str) -> List[dict]:
        """使用领域特定词典提取实体"""
        domain_dict = self._get_domain_dictionary()
        entities = []
        
        for term, ent_type in domain_dict.items():
            if term in text:
                start = text.find(term)
                entities.append({
                    "word": term,
                    "type": ent_type,
                    "offset": start,
                    "length": len(term)
                })
        
        return entities
    
    def _get_domain_dictionary(self) -> dict:
        """获取领域特定词典"""
        if self.domain == "medical":
            return {
                "糖尿病": "DISEASE",
                "胰岛素": "DRUG",
                "高血压": "DISEASE",
                "心脏病": "DISEASE",
                "CT扫描": "TEST",
                "MRI": "TEST",
                "阿司匹林": "DRUG",
                "手术": "TREATMENT",
            }
        elif self.domain == "finance":
            return {
                "阿里巴巴": "COMPANY",
                "腾讯": "COMPANY",
                "股票": "CONCEPT",
                "汇率": "CONCEPT",
                "GDP": "INDICATOR",
                "通货膨胀": "CONCEPT",
                "投资": "ACTION",
                "并购": "ACTION",
            }
        return {}
    
    def extract_relations(self, text: str, entities: List[dict]) -> List[Tuple[str, str, str]]:
        """
        提取实体之间的关系
        :param text: 原始文本
        :param entities: 实体列表 [{'word': '实体', 'type': '类型'}]
        :return: 关系三元组列表 [(头实体, 关系, 尾实体)]
        """
        entity_words = [e['word'] for e in entities]
        if len(entity_words) < 2:
            return []
        
        triplets = []
        
        # 使用规则方法提取简单关系
        triplets.extend(self._rule_based_relation_extraction(text, entity_words))
        
        # 使用模型方法提取复杂关系
        if self.relation_model:
            triplets.extend(self._model_based_relation_extraction(text, entity_words))
        
        return triplets
    
    def _rule_based_relation_extraction(self, text: str, entities: List[str]) -> List[Tuple[str, str, str]]:
        """
        基于规则的关系抽取
        :param text: 原始文本
        :param entities: 实体列表
        :return: 关系三元组列表
        """
        triplets = []
        
        # 1. 共现关系：在同一句子中出现的实体
        sentences = re.split(r'[。！？；]', text)
        for sentence in sentences:
            sentence_entities = [e for e in entities if e in sentence]
            if len(sentence_entities) > 1:
                for i in range(len(sentence_entities)):
                    for j in range(i+1, len(sentence_entities)):
                        triplets.append((sentence_entities[i], "相关", sentence_entities[j]))
        
        # 2. 特定模式匹配
        patterns = self.domain_config.get("relation_patterns", [])
        if not patterns:
            # 默认模式
            patterns = [
                (r"(\w+)(?:属于|是)(\w+)", "属于"),
                (r"(\w+)(?:包含|包括)(\w+)", "包含"),
                (r"(\w+)(?:影响|导致)(\w+)", "影响"),
                (r"(\w+)(?:需要|依赖)(\w+)", "依赖"),
                (r"(\w+)(?:类似|相似)(\w+)", "相似"),
                (r"(\w+)(?:优于|胜过)(\w+)", "优于"),
                (r"(\w+)(?:可以替代|可以替换)(\w+)", "替代")
            ]
        
        for pattern, relation in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entity1, entity2 = match.group(1), match.group(2)
                if entity1 in entities and entity2 in entities:
                    triplets.append((entity1, relation, entity2))
        
        # 去重
        unique_triplets = []
        seen = set()
        for trip in triplets:
            trip_key = (trip[0].lower(), trip[1].lower(), trip[2].lower())
            if trip_key not in seen:
                seen.add(trip_key)
                unique_triplets.append(trip)
        
        return unique_triplets
    
    def _model_based_relation_extraction(self, text: str, entities: List[str]) -> List[Tuple[str, str, str]]:
        """
        基于深度学习模型的关系抽取
        :param text: 原始文本
        :param entities: 实体列表
        :return: 关系三元组列表
        """
        triplets = []
        
        # 创建实体对
        entity_pairs = [(e1, e2) for i, e1 in enumerate(entities) 
                       for j, e2 in enumerate(entities) if i != j]
        
        # 为每个实体对生成输入
        for head, tail in entity_pairs:
            # 在文本中标记实体
            marked_text = text.replace(head, f"[E1]{head}[/E1]", 1)
            marked_text = marked_text.replace(tail, f"[E2]{tail}[/E2]", 1)
            
            # 准备模型输入
            inputs = self.relation_tokenizer(
                marked_text,
                padding="max_length",
                truncation=True,
                max_length=256,
                return_tensors="pt"
            )
            
            # 移动到GPU（如果可用）
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # 模型预测
            with torch.no_grad():
                outputs = self.relation_model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)
                prediction = torch.argmax(probabilities, dim=-1).item()
            
            # 忽略"无关系"预测
            relation_labels = self.domain_config["relation_labels"]
            if prediction > 0 and prediction < len(relation_labels):
                relation = relation_labels[prediction]
                triplets.append((head, relation, tail))
        
        return triplets

    def extract_entities_relations(self, text: str) -> List[Tuple[str, str, str]]:
        """
        从文本中提取实体和关系
        :param text: 输入文本
        :return: 三元组列表 [(头实体, 关系, 尾实体)]
        """
        # 步骤1: 实体识别
        entities = self.extract_entities(text)
        
        # 步骤2: 关系抽取
        triplets = self.extract_relations(text, entities)
        
        return triplets
    

def create_unstructured_db_new(db_name: str, label_name: list, enable_kg: bool = True, domain: str = "general"):
    """创建非结构化知识库索引（优化Markdown分块，确保格式完整），并集成知识图谱功能
    
    Args:
        db_name: 知识库名称
        label_name: 类目名称列表
        enable_kg: 是否启用知识图谱构建（默认为True）
        domain: 知识领域（'general'通用, 'medical'医疗, 'finance'金融等）
    """
    print(f"知识库名称为：{db_name}，类目名称为：{label_name}，知识图谱启用：{enable_kg}，领域：{domain}")
    
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
    
    # 知识图谱数据结构
    kg_data = {
        "triplets": [],  # 存储三元组 [{"head": "实体1", "relation": "关系", "tail": "实体2", "source_doc": "文档ID"}, ...]
        "entity_index": defaultdict(list),  # 实体到文档块的映射 {"实体": [doc_id1, doc_id2]}
        "doc_entities": defaultdict(list),  # 文档块到实体的映射 {doc_id: ["实体1", "实体2"]}
        "entity_types": defaultdict(str),   # 实体类型信息 {"实体": "类型"}
    }
    
    # 初始化知识提取器
    knowledge_extractor = None
    if enable_kg:
        try:
            knowledge_extractor = KnowledgeExtractor(domain=domain)
            print(f"已初始化知识提取器，领域: {domain}")
        except ImportError:
            print("警告：无法导入KnowledgeExtractor，知识图谱功能将受限")
            enable_kg = False
        except Exception as e:
            print(f"初始化知识提取器时出错: {str(e)}")
            enable_kg = False
    
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
    total_chunks = 0
    processed_files = 0
    
    for label in label_name:
        label_path = os.path.join(CATEGORY_PATH, label)
        if not os.path.exists(label_path):
            print(f"类目路径不存在: {label_path}")
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
                    total_chunks += len(chunks)
                    
                    for chunk_index, chunk in enumerate(chunks):
                        # 复制元数据，避免引用问题
                        chunk_metadata = base_metadata.copy()
                        
                        # 检查是否包含图片
                        chunk_metadata['has_image'] = any(
                            tag in chunk for tag in ['![', '<img', '! [', '图像：']
                        )
                        
                        # 检查是否包含代码块
                        chunk_metadata['has_code'] = '```' in chunk
                        
                        # 生成文档ID（使用文件路径和内容哈希）
                        chunk_hash = hashlib.md5(chunk.encode('utf-8')).hexdigest()[:8]
                        doc_id = f"{os.path.basename(file_path)}_{chunk_index}_{chunk_hash}"
                        
                        # 知识图谱处理
                        entities_in_chunk = []
                        if enable_kg and knowledge_extractor:
                            try:
                                # 从文本块中提取实体和关系
                                triplets = knowledge_extractor.extract_entities_relations(chunk)
                                
                                # 存储三元组并建立索引
                                entities_in_chunk = set()
                                for triplet in triplets:
                                    # 添加到三元组列表
                                    kg_data["triplets"].append({
                                        "head": triplet[0],
                                        "relation": triplet[1],
                                        "tail": triplet[2],
                                        "source_doc": doc_id
                                    })
                                    
                                    # 添加实体到索引
                                    entities_in_chunk.add(triplet[0])
                                    entities_in_chunk.add(triplet[2])
                                
                                # 更新实体索引
                                for entity in entities_in_chunk:
                                    kg_data["entity_index"][entity].append(doc_id)
                                
                                # 更新文档实体映射
                                kg_data["doc_entities"][doc_id] = list(entities_in_chunk)
                                
                                # 在元数据中添加实体信息
                                chunk_metadata['entities'] = list(entities_in_chunk)
                            except Exception as e:
                                print(f"知识提取出错: {str(e)}")
                                # 即使出错也继续处理文档
                        
                        document = Document(
                            text=chunk,
                            metadata=chunk_metadata,
                            id_=doc_id
                        )
                        documents.append(document)
                    
                    processed_files += 1
                    if processed_files % 10 == 0:
                        print(f"已处理 {processed_files} 个文件，当前文件分割为 {len(chunks)} 个块")
                else:
                    # 其他文件类型使用SimpleDirectoryReader处理
                    reader = SimpleDirectoryReader(input_files=[file_path])
                    docs = reader.load_data()
                    
                    for doc_index, doc in enumerate(docs):
                        # 添加元数据
                        doc.metadata.update({
                            'db_name': db_name,
                            'category': label,
                            'data_type': 'unstructured',
                            'has_image': False,
                            'has_code': False
                        })
                        
                        # 生成文档ID
                        doc_id = f"{os.path.basename(file_path)}_{doc_index}"
                        
                        # 知识图谱处理（其他文件类型）
                        entities_in_doc = []
                        if enable_kg and knowledge_extractor:
                            try:
                                triplets = knowledge_extractor.extract_entities_relations(doc.text)
                                entities_in_doc = set()
                                for triplet in triplets:
                                    kg_data["triplets"].append({
                                        "head": triplet[0],
                                        "relation": triplet[1],
                                        "tail": triplet[2],
                                        "source_doc": doc_id
                                    })
                                    entities_in_doc.add(triplet[0])
                                    entities_in_doc.add(triplet[2])
                                
                                for entity in entities_in_doc:
                                    kg_data["entity_index"][entity].append(doc_id)
                                
                                kg_data["doc_entities"][doc_id] = list(entities_in_doc)
                                doc.metadata['entities'] = list(entities_in_doc)
                            except Exception as e:
                                print(f"知识提取出错: {str(e)}")
                        
                        # 分块处理
                        nodes = node_parser.get_nodes_from_documents([doc])
                        total_chunks += len(nodes)
                        
                        for node in nodes:
                            document = Document(
                                text=node.text,
                                metadata=node.metadata.copy(),
                                id_=node.id_
                            )
                            documents.append(document)
                    
                    processed_files += 1
                    if processed_files % 10 == 0:
                        print(f"已处理 {processed_files} 个文件，当前文件分割为 {len(nodes)} 个块")
            except Exception as e:
                import traceback
                error_msg = f"处理文件 {file_path} 时出错: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                continue
    
    print(f"文档处理完成，共处理 {processed_files} 个文件，生成 {len(documents)} 个文档块")
    
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
        print(f"已处理 {min(i+batch_size, len(documents))}/{len(documents)} 个文档块")
    
    # 保存索引
    if index:
        db_path = os.path.join(BASE_PATH, db_name)
        os.makedirs(db_path, exist_ok=True)
        index.storage_context.persist(db_path)
        
        # 保存知识图谱数据
        if enable_kg and kg_data["triplets"]:
            save_knowledge_graph(db_name, kg_data)
            print(f"知识图谱包含 {len(kg_data['triplets'])} 个三元组, {len(kg_data['entity_index'])} 个唯一实体")
        
        print(f"知识库 {db_name} 创建成功，包含 {len(documents)} 个文档块")
        return {
            "status": "success",
            "message": f"知识库 {db_name} 创建成功",
            "details": {
                "total_files": processed_files,
                "total_chunks": len(documents),
                "kg_triplets": len(kg_data["triplets"]) if enable_kg else 0,
                "kg_entities": len(kg_data["entity_index"]) if enable_kg else 0
            }
        }
    else:
        print("没有可处理的文档内容")
        return {
            "status": "error",
            "message": "没有可处理的文档内容"
        }

KG_DIR_NAME="wudi"
def save_knowledge_graph(db_name: str, kg_data: dict):
    """保存知识图谱数据到文件"""
    kg_dir = os.path.join(BASE_PATH, db_name, KG_DIR_NAME)
    os.makedirs(kg_dir, exist_ok=True)
    
    # 转换defaultdict为普通dict以便序列化
    def default_to_regular(d):
        if isinstance(d, defaultdict):
            d = {k: default_to_regular(v) for k, v in d.items()}
        return d
    
    # 保存三元组数据
    with open(os.path.join(kg_dir, "triplets.json"), "w", encoding="utf-8") as f:
        json.dump(kg_data["triplets"], f, ensure_ascii=False, indent=2)
    
    # 保存实体索引
    with open(os.path.join(kg_dir, "entity_index.json"), "w", encoding="utf-8") as f:
        json.dump(default_to_regular(kg_data["entity_index"]), f, ensure_ascii=False, indent=2)
    
    # 保存文档-实体关联
    with open(os.path.join(kg_dir, "doc_entities.json"), "w", encoding="utf-8") as f:
        json.dump(default_to_regular(kg_data["doc_entities"]), f, ensure_ascii=False, indent=2)
    
    # 保存实体类型信息（如果有）
    if "entity_types" in kg_data:
        with open(os.path.join(kg_dir, "entity_types.json"), "w", encoding="utf-8") as f:
            json.dump(default_to_regular(kg_data["entity_types"]), f, ensure_ascii=False, indent=2)
    
    print(f"知识图谱已保存: {kg_dir}")