import subprocess
import sys
import os
from pathlib import Path

def run_metagpt():
    # 配置路径
    conda_env = "metagpt_env"  # 确认这是你的正确环境名称
    conda_path = r"D:\miniconda\Scripts\conda.exe"
    script_dir = r"C:\Users\86150\Desktop\metagpt开发"
    script_path = os.path.join(script_dir, "demo.py")
    config_path = os.path.join(script_dir, "config.yaml")
    
    # 确保配置文件存在
    if not os.path.exists(config_path):
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("""llm:
  api_type: "openai"
  api_key: "sk-your-api-key-here"
  model: "gpt-4"
""")
        print(f"请编辑 {config_path} 填写真实的API密钥")
        return

    # 方法1：直接使用环境中的Python解释器（推荐）
    python_exec = Path(f"D:/miniconda/envs/{conda_env}/python.exe")
    if python_exec.exists():
        cmd = [str(python_exec), script_path]
        print("使用方法1")
    else:
        # 方法2：使用conda run（备用）
        cmd = [conda_path, "run", "-n", conda_env, "python", script_path]
        print("使用方法2")
    try:
        subprocess.run(
            cmd,
            cwd=script_dir,  # 设置工作目录
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
    except subprocess.CalledProcessError as e:
        print(f"执行失败，返回码: {e.returncode}")
    except FileNotFoundError as e:
        print(f"找不到文件: {e.filename}")
        print("请检查：")
        print(f"1. Conda环境路径: D:/miniconda/envs/{conda_env}")
        print(f"2. 脚本路径: {script_path}")

if __name__ == "__main__":
    run_metagpt()