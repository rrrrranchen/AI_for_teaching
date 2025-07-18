from questeval.questeval_metric import QuestEval

# 标准初始化方式（自动处理下载）
questeval = QuestEval(
    task="text2text",  # 或 "qa"
    no_cuda=True      # 如果没有GPU
)
