import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com' 


from bert_score import BERTScorer

# 加载多语言模型（中文需用'bert-base-multilingual-cased'）
scorer = BERTScorer(lang="zh", model_type="bert-base-chinese")

def evaluate_bertscore(candidates, references):
    """ 批量评估生成内容与知识库条目的关联性 """
    P, R, F1 = scorer.score(candidates, references)
    return {
        'bert_precision': P.tolist(),  # 检测生成内容是否基于知识库
        'bert_recall': R.tolist(),    # 检测知识库内容是否被完整覆盖
        'bert_f1': F1.tolist()         # 综合指标
    }

# 示例：对比生成的答案与知识库最佳匹配条目
knowledge_base = ["光合作用需要光照、水和CO2", "线粒体是细胞的能量工厂"]
generated_answer = "植物通过吸收光能、水分和二氧化碳制造养分"
scores = evaluate_bertscore([generated_answer], [knowledge_base[0]]) 
print(scores)