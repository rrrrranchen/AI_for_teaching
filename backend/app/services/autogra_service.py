import os
import re
import logging
import numpy as np
import jieba
import torch
from opencc import OpenCC
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChineseGrader:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.cc = OpenCC('t2s')
        self._init_resources()
        self.model_path = r'C:\\Users\13925\\.cache\\huggingface\\hub\\paraphrase-multilingual-MiniLM-L12-v2'
        
        # 初始化模型
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModel.from_pretrained(self.model_path)
            logger.info("模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            raise RuntimeError("请检查模型文件是否存在且完整")

        # 初始化TF-IDF
        self.tfidf_vectorizer = TfidfVectorizer(
            tokenizer=lambda x: self._preprocess_for_tfidf(x),
            token_pattern=None
        )

    def _init_resources(self):
        """初始化所有资源文件"""
        # 自动创建缺失文件
        self._ensure_file('custom_words.txt')
        self._ensure_file('stopwords_cn.txt')
        self._ensure_file('synonyms.txt')
        
        # 加载自定义词典
        jieba.load_userdict(os.path.join(self.BASE_DIR, 'custom_words.txt'))
        
        # 加载停用词
        with open(os.path.join(self.BASE_DIR, 'stopwords_cn.txt'), encoding='utf-8') as f:
            self.stopwords = set(line.strip() for line in f if line.strip())
            
        # 加载同义词词典
        self.synonym_dict = defaultdict(list)
        with open(os.path.join(self.BASE_DIR, 'synonyms.txt'), encoding='utf-8') as f:
            for line in f:
                parts = re.split(r'[\t ]+', line.strip(), maxsplit=1)
                if len(parts) == 2:
                    word, syns = parts
                    self.synonym_dict[word] = [s.strip() for s in re.split(r'[,， ]+', syns) if s.strip()]

    def _ensure_file(self, filename, default_content=""):
        """确保资源文件存在"""
        path = os.path.join(self.BASE_DIR, filename)
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(default_content)

    def _get_word_pos(self, text):
        """兼容不同jieba版本的词性标注"""
        try:
            import jieba.posseg as pseg
            return [(w.word, w.flag) for w in pseg.cut(text)]
        except (ImportError, AttributeError):
            words = jieba.cut(text)
            return [(w, 'n') for w in words]

    def _preprocess(self, text):
        """使用提供的预处理函数"""
        # 基础清洗
        text = self.cc.convert(text)  
        text = re.sub(r'[^\u4e00-\u9fff\w\s]', '', text)  
        
        # 分词+词性过滤
        word_pos = self._get_word_pos(text)
        words = [w for w, pos in word_pos 
                if pos.startswith(('n', 'v', 'a'))  
                and w not in self.stopwords
                and len(w) > 1]  
        
        # 同义词扩展
        expanded = []
        for word in words:
            expanded.append(word)
            synonyms = self.synonym_dict.get(word, [])
            if synonyms and synonyms[0] != word:
                expanded.append(synonyms[0])
        
        # 去重并按词频排序
        from collections import Counter
        word_counts = Counter(words)
        unique_words = list(set(expanded))
        unique_words.sort(key=lambda x: word_counts.get(x, 0), reverse=True)
        
        return unique_words[:min(20, len(unique_words))] 

    def _preprocess_for_tfidf(self, text):
        """TF-IDF专用的预处理（不扩展同义词）"""
        processed = self._preprocess(text)
        return ' '.join(processed)

    def _get_embedding(self, text):
        """获取文本嵌入向量"""
        try:
            
            preprocessed_text = ' '.join(self._preprocess(text))
            inputs = self.tokenizer(
                preprocessed_text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True,
                max_length=512
            )
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            attention_mask = inputs['attention_mask']
            last_hidden = outputs.last_hidden_state
            expanded_mask = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
            return torch.sum(last_hidden * expanded_mask, 1) / torch.clamp(expanded_mask.sum(1), min=1e-9)
        except Exception as e:
            logger.error(f"获取嵌入失败: {str(e)}")
            return torch.zeros(1, 384)  # 返回零向量防止崩溃

    def _calculate_key_concept_match(self, std_answer, student_answer):
        """计算关键概念匹配度"""
        
        std_concepts = set(self._preprocess(std_answer)[:5])  # 取前5个作为关键概念，其他关键概念提取方法太麻烦了，暂用
        stu_concepts = set(self._preprocess(student_answer)[:5])
        
        
        intersection = std_concepts.intersection(stu_concepts)
        match_ratio = len(intersection) / len(std_concepts) if len(std_concepts) > 0 else 0.0
        
        return match_ratio

    def grade(self, std_answer, student_answer, max_score=10):
        """完整的评分流程"""
        try:
            # 预处理（标准答案和学生答案）
            pre_std = self._preprocess(std_answer)
            pre_stu = self._preprocess(student_answer)
            
            # 语义相似度计算
            emb_std = self._get_embedding(std_answer).numpy()
            emb_stu = self._get_embedding(student_answer).numpy()
            semantic_sim = cosine_similarity(emb_std, emb_stu)[0][0]
            
            # TF-IDF相似度计算（使用不扩展同义词的预处理）
            tfidf_std = self._preprocess_for_tfidf(std_answer)
            tfidf_stu = self._preprocess_for_tfidf(student_answer)
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([tfidf_std, tfidf_stu])
            tfidf_sim = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0] if tfidf_matrix.shape[1] > 0 else 0.0
            
            # 长度匹配度
            len_ratio = min(len(student_answer)/len(std_answer), 1.0) if len(std_answer) > 0 else 0.0
            
            # 关键概念匹配度
            key_concept_match = self._calculate_key_concept_match(std_answer, student_answer)
            
            # 综合评分
            base_score = max_score * (
                0.6 * semantic_sim + 
                0.2 * tfidf_sim + 
                0.1 * len_ratio +
                0.1 * key_concept_match
            )
            
            # 如果关键概念匹配度低于阈值，施加额外惩罚，如果不惩罚，关键概念匹配过低时就会出现分值与人为批改严重不符合的情况
            if key_concept_match < 0.6:
                penalty = max_score * (0.6 - key_concept_match) * 0.5
                final_score = max(base_score - penalty, 0)
            else:
                final_score = base_score
            
            final_score = round(final_score, 1)
            
            return {
                "score": min(final_score, max_score),
                "details": {
                    "预处理-标准答案": ' '.join(pre_std),
                    "预处理-学生答案": ' '.join(pre_stu),
                    "语义相似度": f"{semantic_sim*100:.1f}%",
                    "词汇匹配度": f"{tfidf_sim*100:.1f}%",
                    "长度匹配率": f"{len_ratio*100:.1f}%",
                    "关键概念匹配度": f"{key_concept_match*100:.1f}%",
                }
            }
            
        except Exception as e:
            logger.error(f"评分出错: {str(e)}", exc_info=True)
            return {
                "score": 0,
                "error": str(e),
                "advice": [
                    "检查输入文本是否有效",
                    f"确认模型路径存在: {self.model_path}",
                    "查看日志获取详细信息"
                ]
            }
def main():
    # 创建ChineseGrader实例
    grader = ChineseGrader()
    
    # 定义标准答案和学生答案
    std_answer = "这是标准答案，包含了一些关键概念和信息。"
    student_answer = "这是学生的答案，其中包含了一些与标准答案相似的关键概念。"
    
    try:
        # 调用grade方法进行评分
        result = grader.grade(std_answer, student_answer)
        
        # 打印评分结果
        print("评分结果：")
        print(f"得分：{result['score']}")
        print("详细评分信息：")
        for key, value in result['details'].items():
            print(f"{key}: {value}")
    
    except Exception as e:
        # 如果评分过程中出现异常，打印错误信息
        print(f"评分过程中出现错误：{str(e)}")
        print("请检查日志获取详细信息")

if __name__ == "__main__":
    main()

