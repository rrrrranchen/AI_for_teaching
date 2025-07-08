# 辅助函数
def extract_keywords(text):
    """从文本中提取关键词"""
    if not text:
        return set()
    
    import jieba
    from collections import Counter
    

    stopwords = {'的', '了', '和', '是', '在', '我', '有', '你', '这', '那'}
    
    words = jieba.cut(text)
    keywords = [word for word in words if len(word) > 1 and word not in stopwords]
    
    # 取频率最高的10个词
    top_keywords = [word for word, count in Counter(keywords).most_common(10)]
    
    return set(top_keywords)


def calculate_keyword_match(keywords1, keywords2):
    """计算两个关键词集合的匹配度"""
    if not keywords1 or not keywords2:
        return 0.0
    
    intersection = keywords1 & keywords2
    union = keywords1 | keywords2
    
    # Jaccard相似度
    return len(intersection) / len(union) if union else 0.0