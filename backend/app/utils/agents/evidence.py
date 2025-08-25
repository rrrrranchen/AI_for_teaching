from hashlib import sha256
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
import torch
from transformers import BertModel, BertTokenizer
import networkx as nx
from collections import defaultdict
from metagpt.schema import Message


# 加载预训练模型
nlp = spacy.load("zh_core_web_md")
bert_tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
bert_model = BertModel.from_pretrained('bert-base-chinese')



class EvidenceChainValidator:
    """端到端证据链验证器"""
    def __init__(self, kb_client):
        self.kb = kb_client
        self.claim_graph = nx.DiGraph()
        self.entity_index = defaultdict(list)
        
    def process_message(self, message: Message):
        """处理消息并构建证据链"""
        try:
            data = json.loads(message.content)
            claims = data.get("claims", [])
            
            for claim in claims:
                claim_id = f"claim_{sha256(claim['statement'].encode()).hexdigest()[:8]}"
                self.claim_graph.add_node(claim_id, 
                                         type="claim", 
                                         content=claim['statement'])
                
                # 添加证据边
                for evidence in claim.get("evidence", []):
                    evidence_id = f"ev_{evidence['doc_id']}_{evidence['para_idx']}"
                    self.claim_graph.add_node(evidence_id, 
                                             type="evidence", 
                                             content=self._get_evidence_text(evidence))
                    self.claim_graph.add_edge(evidence_id, claim_id, 
                                             rel="supports", 
                                             strength=evidence['support_score'])
                
                # 提取实体并索引
                doc = nlp(claim['statement'])
                for ent in doc.ents:
                    entity_id = f"ent_{ent.text}"
                    self.entity_index[entity_id].append(claim_id)
                    self.claim_graph.add_node(entity_id, type="entity", label=ent.label_)
                    self.claim_graph.add_edge(claim_id, entity_id, rel="mentions")
        
        except json.JSONDecodeError:
            # 处理非结构化消息
            doc = nlp(message.content)
            for sent in doc.sents:
                if len(sent) > 10:  # 仅处理有意义的句子
                    claim_id = f"uc_{sha256(sent.text.encode()).hexdigest()[:8]}"
                    self.claim_graph.add_node(claim_id, 
                                             type="unverified_claim", 
                                             content=sent.text,
                                             status="unsubstantiated")
    
    def _get_evidence_text(self, evidence: dict) -> str:
        """获取证据文本"""
        return self.kb.get_text_fragment(
            evidence['doc_id'],
            evidence['start'],
            evidence['end'],
            evidence['version']
        )
    
    def validate_chain(self, claim_id: str, depth=3) -> dict:
        """验证证据链的可信度"""
        if claim_id not in self.claim_graph:
            return {"status": "not_found"}
        
        # 收集所有相关节点
        relevant_nodes = set()
        relevant_nodes.add(claim_id)
        
        # 向上追溯证据
        for _ in range(depth):
            new_nodes = set()
            for node in relevant_nodes:
                predecessors = list(self.claim_graph.predecessors(node))
                new_nodes.update(predecessors)
            relevant_nodes.update(new_nodes)
        
        # 向下追溯实体
        for _ in range(depth):
            new_nodes = set()
            for node in relevant_nodes:
                successors = list(self.claim_graph.successors(node))
                new_nodes.update(successors)
            relevant_nodes.update(new_nodes)
        
        # 计算子图可信度
        subgraph = self.claim_graph.subgraph(relevant_nodes)
        return self._calculate_subgraph_trust(subgraph)
    
    def _calculate_subgraph_trust(self, subgraph: nx.DiGraph) -> dict:
        """计算子图的可信度指标"""
        # 收集所有声明和证据
        claims = [n for n, attr in subgraph.nodes(data=True) 
                 if attr['type'] in ["claim", "unverified_claim"]]
        evidences = [n for n, attr in subgraph.nodes(data=True) 
                    if attr['type'] == "evidence"]
        
        # 计算基本指标
        result = {
            "total_claims": len(claims),
            "supported_claims": 0,
            "unsupported_claims": 0,
            "evidence_count": len(evidences),
            "evidence_coverage": 0.0,
            "semantic_consistency": 0.0,
            "contradiction_score": 0.0
        }
        
        # 计算支持率
        for claim in claims:
            if subgraph.nodes[claim].get('status') == "substantiated":
                result["supported_claims"] += 1
            else:
                result["unsupported_claims"] += 1
        
        # 计算证据覆盖率
        if claims:
            result["evidence_coverage"] = result["supported_claims"] / len(claims)
        
        # 计算语义一致性
        claim_texts = [subgraph.nodes[c]['content'] for c in claims]
        evidence_texts = [subgraph.nodes[e]['content'] for e in evidences]
        result["semantic_consistency"] = self._calculate_semantic_consistency(
            claim_texts, evidence_texts
        )
        
        # 计算矛盾分数
        result["contradiction_score"] = self._detect_contradictions(subgraph)
        
        # 总体可信度分数（加权平均）
        weights = {
            'evidence_coverage': 0.4,
            'semantic_consistency': 0.3,
            'contradiction_score': 0.3
        }
        result["trust_score"] = (
            weights['evidence_coverage'] * result["evidence_coverage"] +
            weights['semantic_consistency'] * result["semantic_consistency"] +
            weights['contradiction_score'] * (1 - result["contradiction_score"])
        )
        
        return result
    
    def _calculate_semantic_consistency(self, claims: list, evidences: list) -> float:
        """计算声明与证据之间的语义一致性"""
        if not claims or not evidences:
            return 0.0
        
        # 使用TF-IDF向量化
        vectorizer = TfidfVectorizer()
        all_texts = claims + evidences
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # 计算相似度矩阵
        similarity_matrix = cosine_similarity(
            tfidf_matrix[:len(claims)], 
            tfidf_matrix[len(claims):]
        )
        
        # 获取每个声明与最相关证据的相似度
        max_similarities = np.max(similarity_matrix, axis=1)
        return float(np.mean(max_similarities))
    
    def _detect_contradictions(self, subgraph: nx.DiGraph) -> float:
        """检测子图中的矛盾"""
        claims = [n for n, attr in subgraph.nodes(data=True) 
                 if attr['type'] in ["claim", "unverified_claim"]]
        
        if len(claims) < 2:
            return 0.0
        
        # 使用BERT获取声明嵌入
        claim_texts = [subgraph.nodes[c]['content'] for c in claims]
        embeddings = self._get_bert_embeddings(claim_texts)
        
        # 计算矛盾分数
        contradiction_matrix = 1 - cosine_similarity(embeddings)
        np.fill_diagonal(contradiction_matrix, 0)  # 忽略自比较
        
        # 取最显著矛盾
        max_contradiction = np.max(contradiction_matrix)
        return float(max_contradiction)
    
    def _get_bert_embeddings(self, texts: list) -> np.ndarray:
        """获取BERT嵌入向量"""
        inputs = bert_tokenizer(
            texts, 
            padding=True, 
            truncation=True, 
            return_tensors="pt", 
            max_length=128
        )
        
        with torch.no_grad():
            outputs = bert_model(**inputs)
        
        # 使用平均池化获取句子嵌入
        embeddings = outputs.last_hidden_state.mean(dim=1).numpy()
        return embeddings

class KnowledgeSupportValidator:
    """数学化的支持度验证算法"""
    def __init__(self, kb_client):
        self.kb = kb_client
        self.vectorizer = TfidfVectorizer()
        self.claim_cache = {}
    
    def validate_claim(self, claim: str, evidence_list: list, context: str = "") -> dict:
        """
        验证声明与证据的支持度
        返回包含多个指标的验证结果
        """
        # 基本验证结果
        result = {
            "claim": claim,
            "evidence_count": len(evidence_list),
            "direct_support": 0.0,
            "contextual_support": 0.0,
            "semantic_coherence": 0.0,
            "source_diversity": 0.0,
            "temporal_relevance": 0.0,
            "overall_score": 0.0
        }
        
        if not evidence_list:
            return result
        
        # 准备验证数据
        evidence_texts = []
        source_ids = set()
        timestamps = []
        
        for evidence in evidence_list:
            # 获取证据文本
            evidence_text = self._get_evidence_text(evidence)
            evidence_texts.append(evidence_text)
            
            # 收集元数据
            source_ids.add(evidence['doc_id'])
            timestamps.append(evidence.get('timestamp', 0))
        
        # 1. 直接支持度计算
        result["direct_support"] = self._calculate_direct_support(
            claim, evidence_texts
        )
        
        # 2. 上下文支持度
        if context:
            result["contextual_support"] = self._calculate_contextual_support(
                claim, evidence_texts, context
            )
        
        # 3. 语义连贯性
        result["semantic_coherence"] = self._calculate_semantic_coherence(
            evidence_texts
        )
        
        # 4. 来源多样性
        result["source_diversity"] = len(source_ids) / len(evidence_list)
        
        # 5. 时间相关性
        result["temporal_relevance"] = self._calculate_temporal_relevance(timestamps)
        
        # 综合分数（加权平均）
        weights = {
            "direct_support": 0.4,
            "contextual_support": 0.2 if context else 0.0,
            "semantic_coherence": 0.2,
            "source_diversity": 0.1,
            "temporal_relevance": 0.1
        }
        
        # 调整权重总和为1
        total_weight = sum(weights.values())
        result["overall_score"] = sum(
            result[metric] * weights[metric] for metric in weights
        ) / total_weight
        
        return result
    
    def _get_evidence_text(self, evidence: dict) -> str:
        """获取证据文本（带缓存）"""
        cache_key = f"{evidence['doc_id']}_{evidence['para_idx']}_{evidence['start']}_{evidence['end']}"
        if cache_key in self.claim_cache:
            return self.claim_cache[cache_key]
        
        text = self.kb.get_text_fragment(
            evidence['doc_id'],
            evidence['start'],
            evidence['end'],
            evidence['version']
        )
        self.claim_cache[cache_key] = text
        return text
    
    def _calculate_direct_support(self, claim: str, evidence_texts: list) -> float:
        """计算直接支持度"""
        # 使用TF-IDF向量化
        all_texts = [claim] + evidence_texts
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)
        
        # 计算相似度
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        return float(np.max(similarity_matrix))
    
    def _calculate_contextual_support(self, claim: str, evidence_texts: list, context: str) -> float:
        """计算上下文支持度"""
        # 准备上下文增强的声明
        enhanced_claim = f"{context} {claim}"
        
        # 向量化
        vectorizer = TfidfVectorizer()
        all_texts = [enhanced_claim] + evidence_texts
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # 计算相似度
        similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        return float(np.mean(similarity_matrix))
    
    def _calculate_semantic_coherence(self, evidence_texts: list) -> float:
        """计算证据之间的语义连贯性"""
        if len(evidence_texts) < 2:
            return 1.0  # 单一证据默认完全一致
        
        # 向量化所有证据
        tfidf_matrix = self.vectorizer.fit_transform(evidence_texts)
        
        # 计算证据间的平均相似度
        similarity_matrix = cosine_similarity(tfidf_matrix)
        np.fill_diagonal(similarity_matrix, 0)  # 忽略自比较
        
        # 计算平均非对角线元素
        n = len(evidence_texts)
        return float(np.sum(similarity_matrix) / (n * (n - 1)))
    
    

class EnhancedKnowledgeValidator:
    
    def __init__(self, kb_client):
        self.kb = kb_client
        self.support_validator = KnowledgeSupportValidator(kb_client)
        self.chain_validator = EvidenceChainValidator(kb_client)
        self.entity_graph = nx.Graph()
    
    def process_message(self, message: Message):
        """处理消息并更新验证状态"""
        self.chain_validator.process_message(message)
        
        # 如果是结构化消息，更新支持度分数
        try:
            data = json.loads(message.content)
            claims = data.get("claims", [])
            
            for claim in claims:
                evidence_list = claim.get("evidence", [])
                support_result = self.support_validator.validate_claim(
                    claim['statement'], 
                    evidence_list,
                    context=message.context
                )
                
                # 更新声明状态
                claim['support_score'] = support_result['overall_score']
                claim['substantiated'] = support_result['overall_score'] >= 0.7
                
                # 更新证据链验证器
                claim_id = f"claim_{sha256(claim['statement'].encode()).hexdigest()[:8]}"
                if claim_id in self.chain_validator.claim_graph:
                    self.chain_validator.claim_graph.nodes[claim_id]['status'] = \
                        "substantiated" if claim['substantiated'] else "unsubstantiated"
        
        except json.JSONDecodeError:
           
            pass
    
    def validate_entity(self, entity_name: str) -> dict:
        """验证与实体相关的所有声明"""
        entity_id = f"ent_{entity_name}"
        related_claims = self.chain_validator.entity_index.get(entity_id, [])
        
        if not related_claims:
            return {"status": "entity_not_found"}
        
        # 收集所有相关声明
        results = []
        for claim_id in related_claims:
            claim_data = self.chain_validator.claim_graph.nodes[claim_id]
            evidence_count = len(list(
                self.chain_validator.claim_graph.predecessors(claim_id)
            ))
            
            results.append({
                "claim": claim_data['content'],
                "support_score": claim_data.get('support_score', 0),
                "status": claim_data.get('status', 'unverified'),
                "evidence_count": evidence_count
            })
        
        # 计算实体可信度指标
        substantiated = [r for r in results if r['status'] == 'substantiated']
        total_score = sum(r['support_score'] for r in substantiated)
        
        return {
            "entity": entity_name,
            "total_claims": len(results),
            "substantiated_claims": len(substantiated),
            "average_support": total_score / len(substantiated) if substantiated else 0,
            "claims": results
        }
    
    def get_trust_report(self, min_score=0.7) -> dict:
        """生成系统级可信度报告"""
        all_claims = [n for n, attr in self.chain_validator.claim_graph.nodes(data=True)
                     if attr['type'] in ['claim', 'unverified_claim']]
        
        report = {
            "total_claims": len(all_claims),
            "substantiated_claims": 0,
            "unsubstantiated_claims": 0,
            "average_support": 0.0,
            "high_confidence_claims": [],
            "low_confidence_claims": []
        }
        
        total_score = 0
        for claim_id in all_claims:
            node = self.chain_validator.claim_graph.nodes[claim_id]
            score = node.get('support_score', 0)
            status = node.get('status', 'unverified')
            
            if status == 'substantiated':
                report["substantiated_claims"] += 1
                total_score += score
            else:
                report["unsubstantiated_claims"] += 1
            
            if score >= min_score:
                report["high_confidence_claims"].append({
                    "claim": node['content'],
                    "score": score,
                    "evidence_count": len(list(
                        self.chain_validator.claim_graph.predecessors(claim_id)
                    ))
                })
            elif score > 0:
                report["low_confidence_claims"].append({
                    "claim": node['content'],
                    "score": score,
                    "evidence_count": len(list(
                        self.chain_validator.claim_graph.predecessors(claim_id)
                    ))
                })
        
        if report["substantiated_claims"] > 0:
            report["average_support"] = total_score / report["substantiated_claims"]
        
        return report
