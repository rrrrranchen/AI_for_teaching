from questeval.questeval_metric import QuestEval

questeval = QuestEval(task="text2text")  # 或"qa"模式

def check_consistency(generated_text, knowledge_context):
    score = questeval.compute(
        sources=[knowledge_context],
        predictions=[generated_text]
    )['f1']  # 使用F1值综合判断
    return score > 0.6  # 可调整阈值

# 示例：检查历史事实描述
history_fact = "秦始皇于公元前221年统一中国"
generated_desc = "中国在公元前三世纪由嬴政完成统一"
is_consistent = check_consistency(generated_desc, history_fact)
