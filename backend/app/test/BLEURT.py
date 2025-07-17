import evaluate

# 自动处理模型下载和加载
bleurt = evaluate.load("bleurt", module_type="metric")

# 计算分数
references = ["The cat sits on the mat"]
candidates = ["There is a cat on the mat"]
results = bleurt.compute(predictions=candidates, references=references)

print(results["scores"])  # 输出: [-0.12]
