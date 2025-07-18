import os
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import batch_to_device

import logging
import warnings

import torch

# 配置日志系统
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 忽略特定警告
warnings.filterwarnings('ignore', category=UserWarning, module='sentence_transformers')

@dataclass
class CoverageResult:
    """结构化结果输出"""
    score: float
    matched: List[str]
    missing: List[str]
    similarity_map: Dict[str, float]
    threshold: float

class SemanticGrader:
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化语义评分器
        
        参数:
            model_path: 本地模型路径，若为None则使用在线模型
        """
        model_path = r'C:\\Users\13925\\.cache\\huggingface\\hub\\paraphrase-multilingual-MiniLM-L12-v2'
        self.model = self._load_model(model_path)
        self.default_threshold = 0.7
        self.batch_size = 64
        self.normalize = True

    def _load_model(self, model_path: str) -> SentenceTransformer:
        """安全加载模型"""
        try:
            if os.path.exists(model_path):
                logger.info(f"Loading local model from {model_path}")
                return SentenceTransformer(model_path)
            logger.info(f"Downloading online model: {model_path}")
            return SentenceTransformer(model_path)
        except Exception as e:
            logger.error(f"Model loading failed: {str(e)}")
            raise RuntimeError(f"无法加载模型: {model_path}")

    def _safe_encode(self, texts: List[str]) -> np.ndarray:
        """带错误处理的批量编码"""
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                convert_to_tensor=True,
                normalize_embeddings=self.normalize
            )
            # 修改这行代码 ↓
            return embeddings.cpu().numpy() if torch.is_tensor(embeddings) else embeddings
        except Exception as e:
            logger.error(f"文本编码失败: {str(e)}")
            raise RuntimeError("文本处理错误，请检查输入内容")


    def calculate_coverage(
        self,
        text: str,
        concepts: List[str],
        threshold: Optional[float] = None
    ) -> CoverageResult:
        """
        计算文本对知识概念的覆盖情况
        
        参数:
            text: 待分析文本
            concepts: 知识概念列表
            threshold: 相似度判定阈值
            
        返回:
            CoverageResult 结构体
        """
        if not concepts:
            return CoverageResult(0.0, [], [], {}, threshold or self.default_threshold)

        threshold = threshold or self.default_threshold
        
        try:
            # 批量编码处理
            text_embed = self._safe_encode([text])[0]
            concept_embeds = self._safe_encode(concepts)
            
            # 计算相似度矩阵
            sim_matrix = cosine_similarity(
                text_embed.reshape(1, -1),
                concept_embeds
            )[0]
            
            # 分析匹配结果
            matched_mask = sim_matrix >= threshold
            matched_indices = np.where(matched_mask)[0]
            
            return CoverageResult(
                score=float(np.mean(matched_mask)),
                matched=[concepts[i] for i in matched_indices],
                missing=[concepts[i] for i in range(len(concepts)) if not matched_mask[i]],
                similarity_map=dict(zip(concepts, sim_matrix.tolist())),
                threshold=threshold
            )
            
        except Exception as e:
            logger.error(f"覆盖率计算失败: {str(e)}", exc_info=True)
            raise RuntimeError("语义分析过程中发生错误")

# 使用示例
if __name__ == "__main__":
    # 初始化评分器
    grader = SemanticGrader()
    
    # 测试数据
    sample_text = "深度学习模型使用神经网络进行特征提取"
    knowledge_base = [
        "机器学习", 
        "神经网络", 
        "卷积运算",
        "梯度下降",
        "自然语言处理"
    ]
    
    # 执行分析
    try:
        result = grader.calculate_coverage(sample_text, knowledge_base)
        
        # 输出结果
        print(f"知识覆盖率: {result.score:.1%} (阈值={result.threshold})")
        print("匹配的概念:", result.matched)
        print("缺失的概念:", result.missing)
        
        # 输出相似度详情
        print("\n相似度详情:")
        for concept, score in sorted(result.similarity_map.items(), key=lambda x: -x[1]):
            print(f"- {concept}: {score:.3f}")
            
    except Exception as e:
        print(f"分析失败: {str(e)}")
