import subprocess
import sys
import os
import json
from pathlib import Path

def run_metagpt(
    objective: str,
    teaching_content: str,
    knowledge: str = "默认知识库内容",  # 新增知识库参数
    student_feedback: list = None,
    investment: float = 5.0,          # 新增投资参数
    n_round: int = 100,               # 新增轮次参数
    conda_env: str = "metagpt_env",
    conda_path: str = r"D:\miniconda\Scripts\conda.exe",
    script_dir: str = r"d:\AI_for_teaching\backend\app\agents"
):
    """运行MetaGPT教学设计的增强版本
    
    Args:
        objective: 教学目标描述
        teaching_content: 教学内容描述
        knowledge: 知识库检索结果 (新增)
        student_feedback: 学生反馈数据列表
        investment: 团队投资金额 (新增)
        n_round: 模拟运行轮次 (新增)
        conda_env: Conda环境名称
        conda_path: Conda可执行文件路径
        script_dir: 脚本目录路径
    
    Returns:
        执行输出内容或None(失败时)
    """
    # 准备完整参数集
    params = {
        "objective": objective,
        "teaching_content": teaching_content,
        "knowledge": knowledge,  # 传递知识库参数
        "investment": investment,
        "n_round": n_round,
        "feed_back": json.dumps(student_feedback or [{
            "student_id": "S001",
            "questions": [{
                "question": "示例问题",
                "answer": "示例答案"
            }]
        }], ensure_ascii=False)
    }
    
    # 创建临时文件路径
    temp_file_path = os.path.join(script_dir, "temp_params.json")
    with open(temp_file_path, "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False)
    
    # 构建Python命令
    py_command = f"""
import json
import asyncio
import sys
import os

# 修复中文路径问题
sys.path.append(os.path.dirname(__file__))

try:
    from teaching_design_generator_with_optimizer import main
except ImportError as e:
    print(f"导入错误: {{e}}")
    print("当前目录:", os.getcwd())
    print("sys.path:", sys.path)
    raise

with open(r'{temp_file_path}', 'r', encoding='utf-8') as f:
    params = json.load(f)

asyncio.run(main(**params))
"""
    
    # 将命令写入临时脚本文件
    script_file = os.path.join(script_dir, "temp_script.py")
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(py_command)
    
    # 方法1：直接使用环境中的Python解释器
    python_exec = Path(f"D:/miniconda/envs/{conda_env}/python.exe")
    if python_exec.exists():
        cmd = [str(python_exec), script_file]
        print("使用方法1")
    else:
        # 方法2：使用conda run（备用）
        cmd = [conda_path, "run", "-n", conda_env, "python", script_file]
        print("使用方法2")
    
    try:
        print(f"执行命令: {' '.join(cmd)}")
        print(f"工作目录: {script_dir}")
        
        # 启动子进程并实时输出，显式设置编码为UTF-8
        process = subprocess.Popen(
            cmd,
            cwd=script_dir, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',  # 显式设置编码
            errors='replace',  # 处理编码错误
            bufsize=1
        )
        
        # 实时读取输出
        output_lines = []
        while True:
            line = process.stdout.readline()
            if line == '' and process.poll() is not None:
                break
            if line:
                print(line.strip())
                output_lines.append(line)
        
        # 检查错误
        stderr = process.stderr.read()
        if stderr:
            print("错误输出:")
            print(stderr)
        
        return_code = process.wait()
        if return_code != 0:
            print(f"执行失败，返回码: {return_code}")
            return None
        
        return ''.join(output_lines)
    
    except Exception as e:
        print(f"执行出错: {str(e)}")
        return None
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
        if os.path.exists(script_file):
            try:
                os.remove(script_file)
            except:
                pass

if __name__ == "__main__":
    output = run_metagpt(
        objective= "计算机网络tcp原理",
        teaching_content= "TCP三次握手和四次挥手",
        knowledge= "TCP协议相关知识点...",
        investment= 3.0,
        n_round= 50

    )
    if output:
        print("执行结果！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！:", output)
