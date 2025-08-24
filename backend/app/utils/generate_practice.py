from datetime import datetime
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

# --------------------------------------------------
# 1. 读环境变量
# --------------------------------------------------
load_dotenv()

# --------------------------------------------------
# 2. 初始化 DeepSeek
# --------------------------------------------------
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_base="https://api.deepseek.com/v1",
    openai_api_key="sk-ca9d2a314fda4f8983f61e292a858d17",
    temperature=0.7,  # 增加创造性
)

# --------------------------------------------------
# 3. 构造提示词模板（要求返回 JSON）
# --------------------------------------------------
system_prompt = (
    "你是一个专业的跨学科教育助手，擅长设计各种学科的实验实践题。请根据以下提供的教学内容，生成一个符合教育目标的实验题目。\n\n"
    "输出约束：\n"
    "1. 根据教学内容自行判断学科领域并设计相应的实验题\n"
    "2. 实验题应包含以下结构：\n"
    "   - 任务名称与目标\n"
    "   - 环境要求与材料/数据集\n"
    "   - 分步骤实践指导（含代码/操作步骤）\n"
    "   - 分析报告要求（含数据分析、原理分析、应用建议）\n"
    "   - 考核标准与分值分配\n"
    "   - 教学支撑设计（知识衔接、错误排查、进阶引导）\n"
    "3. 使用Markdown格式输出，代码部分使用代码块\n"
    "4. 确保实验题具有可操作性，适合学生实践\n"
    "5. 必须提供正确的答案和预期结果（correct_answer字段）\n\n"
    "请生成完整的实验题内容，包括正确答案："
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{teaching_content}")
])

# --------------------------------------------------
# 4. 组装链
# --------------------------------------------------
chain = prompt | llm

# --------------------------------------------------
# 5. 定义输出结构
# --------------------------------------------------
class ExperimentOutputParser(JsonOutputParser):
    def parse(self, text: str) -> Dict[str, Any]:
        try:
            # 尝试解析为JSON
            return super().parse(text)
        except:
            # 如果不是JSON格式，返回原始文本
            return {"experiment": text, "correct_answer": "无法解析为JSON格式"}

# --------------------------------------------------
# 6. 主函数：生成实验题
# --------------------------------------------------
def generate_experiment(teaching_content: str, save_dir: Optional[str] = None) -> Dict:
    """
    根据教学内容生成实验题
    
    :param teaching_content: 教学设计内容
    :param save_dir: 保存JSON的目录；None则不保存
    :return: 包含实验题内容和正确答案的字典
    """
    if not teaching_content.strip():
        raise ValueError("教学内容不能为空！")
    
    print(f"✅ 已读取教学内容，共 {len(teaching_content)} 字符，正在请求 DeepSeek…")
    
    # 调用模型生成实验题
    response = chain.invoke({"teaching_content": teaching_content})
    experiment_content = response.content
    
    # 尝试解析JSON格式的响应
    try:
        result = json.loads(experiment_content)
        if "correct_answer" not in result:
            result["correct_answer"] = "模型未提供正确答案"
    except json.JSONDecodeError:
        # 如果不是JSON格式，创建默认结构
        result = {
            "experiment": experiment_content,
            "correct_answer": "模型未提供结构化正确答案，请查看实验题内容中的答案部分"
        }
    
    # 添加元数据
    result.update({
        "generated_at": datetime.now().isoformat(),
        "content_length": len(teaching_content),
        "model": "deepseek-chat"
    })
    
    # 保存到文件
    if save_dir:
        save_path = Path(save_dir).expanduser().resolve()
        save_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON格式
        json_file = save_path / f"experiment_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 保存Markdown格式
        md_file = save_path / f"experiment_{timestamp}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# 实验题\n\n{result.get('experiment', '')}\n\n")
            f.write(f"# 正确答案\n\n{result.get('correct_answer', '')}\n\n")
            f.write(f"---\n\n*生成时间: {result['generated_at']}*\n")
        
        result["_json_file"] = str(json_file.absolute())
        result["_md_file"] = str(md_file.absolute())
        print(f"🎉 实验题已保存至：{result['_json_file']} 和 {result['_md_file']}")
    
    return result

# --------------------------------------------------
# 7. 读取教学内容的辅助函数
# --------------------------------------------------
def read_teaching_content(file_path: str) -> str:
    """
    从文件读取教学内容
    
    :param file_path: 文件路径
    :return: 文件内容
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"读取文件失败: {str(e)}")

# --------------------------------------------------
# 8. 增强版提示词（要求返回JSON格式）
# --------------------------------------------------
def generate_experiment_with_json(teaching_content: str, save_dir: Optional[str] = None) -> Dict:
    """
    使用更明确的JSON格式要求生成实验题
    
    :param teaching_content: 教学设计内容
    :param save_dir: 保存JSON的目录；None则不保存
    :return: 包含实验题内容和正确答案的字典
    """
    # 增强版系统提示词，明确要求JSON格式
    json_system_prompt = (
        "你是一个专业的跨学科教育助手，擅长设计各种学科的实验实践题。请根据以下提供的教学内容，生成一个符合教育目标的实验题目。\n\n"
        "输出格式要求（必须严格遵守）：\n"
        "请返回一个JSON对象，包含以下字段：\n"
        "1. \"experiment\": 实验题的完整内容，使用Markdown格式\n"
        "2. \"correct_answer\": 实验题的正确结果和答案，使用Markdown格式\n"
        "\n"
        "实验题结构要求（experiment字段内容）：\n"
        "- 任务名称与目标\n"
        "- 环境要求与材料/数据集\n"
        "- 分步骤实践指导（含代码/操作步骤）\n"
        "- 分析报告要求（含数据分析、原理分析、应用建议）\n"
        "- 考核标准与分值分配\n"
        "- 教学支撑设计（知识衔接、错误排查、进阶引导）\n"
        "\n"
        "正确答案要求（correct_answer字段内容）：\n"
        "- 如果是编程实验，提供完整的可运行代码和预期输出\n"
        "- 如果是数据分析实验，提供分析过程和结果\n"
        "- 如果是理论问题，提供详细的解释\n"
        "- 使用Markdown格式，代码部分使用代码块\n"
        "\n"
        "注意：根据教学内容自行判断学科领域并设计相应的实验题。"
    )
    
    json_prompt = ChatPromptTemplate.from_messages([
        ("system", json_system_prompt),
        ("human", "{teaching_content}")
    ])
    
    json_chain = json_prompt | llm | JsonOutputParser()
    
    if not teaching_content.strip():
        raise ValueError("教学内容不能为空！")
    
    print(f"✅ 已读取教学内容，共 {len(teaching_content)} 字符，正在请求 DeepSeek（JSON格式）…")
    
    try:
        # 调用模型生成实验题
        result = json_chain.invoke({"teaching_content": teaching_content})
        
        # 确保包含正确答案字段
        if "correct_answer" not in result:
            result["correct_answer"] = "模型未提供正确答案"
        
    except Exception as e:
        print(f"⚠️ JSON格式生成失败，使用普通模式: {e}")
        return generate_experiment(teaching_content, save_dir)
    
    # 添加元数据
    result.update({
        "generated_at": datetime.now().isoformat(),
        "content_length": len(teaching_content),
        "model": "deepseek-chat",
        "format": "json"
    })
    
    # 保存到文件
    if save_dir:
        save_path = Path(save_dir).expanduser().resolve()
        save_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON格式
        json_file = save_path / f"experiment_json_{timestamp}.json"
        filename = os.path.basename(json_file)
        rpath = os.path.join('static','experiments',filename)
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 保存Markdown格式
        md_file = save_path / f"experiment_json_{timestamp}.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# 实验题\n\n{result.get('experiment', '')}\n\n")
            f.write(f"# 正确答案\n\n{result.get('correct_answer', '')}\n\n")
            f.write(f"---\n\n*生成时间: {result['generated_at']}*\n")
        
        result["_json_file"] = str(json_file.absolute())
        result["_md_file"] = str(md_file.absolute())
        result["rpath"] = rpath
        print(f"🎉 实验题已保存至：{result['_json_file']} 和 {result['_md_file']}")
    
    return result

if __name__ == "__main__":
    # 示例: 计算机视觉相关的教学内容
    teaching_content = """
    本课程模块讲解卷积神经网络(CNN)的基本原理和应用。
    重点内容包括：
    - CNN的层次结构（卷积层、池化层、全连接层）
    - 常见CNN架构（LeNet、AlexNet、VGG、ResNet）
    - 图像分类任务实践
    - 使用TensorFlow/Keras实现CNN
    
    学生需要掌握CNN的基本原理，并能够使用框架实现简单的图像分类模型。
    """
    
    # 生成实验题（使用JSON格式）
    print("使用JSON格式生成实验题...")
    result = generate_experiment_with_json(
        teaching_content=teaching_content,
        save_dir="D:/AI_for_teaching/backend/app/static/experiments"
    )
    
    print("\n生成的实验题内容：")
    print(result.get("experiment", ""))
    print("\n正确答案：")
    print(result.get("correct_answer", ""))
    
    if "_json_file" in result:
        print(f"\n文件保存位置：{result['_json_file']}")