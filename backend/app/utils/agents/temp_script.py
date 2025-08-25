
import json
import asyncio
import sys
import os

# 修复中文路径问题
sys.path.append(os.path.dirname(__file__))

try:
    from teaching_design_generator_with_optimizer import main
except ImportError as e:
    print(f"导入错误: {e}")
    print("当前目录:", os.getcwd())
    print("sys.path:", sys.path)
    raise

with open(r'd:\AI_for_teaching\backend\app\agents\temp_params.json', 'r', encoding='utf-8') as f:
    params = json.load(f)

asyncio.run(main(**params))
