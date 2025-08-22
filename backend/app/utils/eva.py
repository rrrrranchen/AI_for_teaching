import os
import json
from typing import Dict
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain
import docx2txt
from datetime import datetime

def approve_report_deepseek(file_path: str, question_content: str = "") -> Dict[str, str]:
    """
    基于 DeepSeek 的实验报告自动审批（支持 PDF / DOCX / DOC）
    包含评分、实践可行性评估，并支持额外传入题目内容辅助判断
    """
    # ---------- 1. 文件读取 ----------
    if not os.path.exists(file_path):
        return {
            "score": "0",
            "compliance": f"文件不存在：{file_path}",
            "feasibility": "无法评估",
            "approval": "审批失败，请检查文件路径是否正确。"
        }

    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            report_text = "\n".join([d.page_content for d in docs])
        elif ext in {".docx", ".doc"}:
            report_text = docx2txt.process(file_path)
            if not report_text.strip():
                raise RuntimeError("文件内容为空")
        else:
            raise ValueError("只支持 .pdf / .docx / .doc 文件")
    except Exception as e:
        return {
            "score": "0",
            "compliance": f"无法读取文件：{e}",
            "feasibility": "无法评估",
            "approval": "审批失败，请检查文件格式或完整性。"
        }

    # ---------- 2. LLM 初始化 ----------
    llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_key="sk-ca9d2a314fda4f8983f61e292a858d17",
        openai_api_base="https://api.deepseek.com/v1",
        temperature=0
    )

    # ---------- 3. Prompt 模板 ----------
    scoring_prompt = PromptTemplate.from_template("""
请对以下实验报告进行综合评分（0-100分）并检查合规性。
题目要求：
{question}

评分标准：
1. 内容完整性（30分）：是否包含实验名称、目的、方法、结果、结论等基本要素
2. 数据支持（25分）：是否有充分的数据或证据支持实验结果
3. 逻辑性（25分）：是否有逻辑错误或不一致之处
4. 格式规范性（20分）：是否符合实验报告的基本格式要求
5. 题目契合度（10分）：是否准确回应了题目要求

合规性检查：
- 检查是否存在严重问题或缺失关键要素

实验报告内容：
{report}

请按以下JSON格式返回：
{{
  "score": "具体分数",
  "compliance": "合规性评价（通过/不通过）",
  "scoring_details": {{
    "content_completeness": "内容完整性评分和评语",
    "data_support": "数据支持评分和评语",
    "logicality": "逻辑性评分和评语",
    "format_standardization": "格式规范性评分和评语",
    "question_relevance": "题目契合度评分和评语"
  }}
}}
""")

    feasibility_prompt = PromptTemplate.from_template("""
请评估以下实验报告的实践可行性。

题目要求：
{question}

实验报告内容：
{report}

评分结果：
{scoring}

请从以下角度评估实践可行性：
1. 实验方法的可重复性
2. 结果的可验证性
3. 实际应用价值
4. 技术实现的难易程度
5. 是否满足题目要求

请按以下格式输出：
可行性评估：高/中/低
详细分析：
- 优势点1
- 潜在问题1
- 改进建议1
...
""")

    approval_prompt = PromptTemplate.from_template("""
基于以下评分结果和可行性评估，给出最终审批意见：

评分结果：
{scoring}

可行性评估：
{feasibility}

请给出审批意见：
- 是否通过审批（通过/不通过）
- 总体评价
- 具体修改建议（如有需要）
- 推荐等级（优秀/良好/合格/不合格）
""")

    # ---------- 4. Chain ----------
    chain = SequentialChain(
        chains=[
            LLMChain(llm=llm, prompt=scoring_prompt, output_key="scoring"),
            LLMChain(llm=llm, prompt=feasibility_prompt, output_key="feasibility"),
            LLMChain(llm=llm, prompt=approval_prompt, output_key="approval")
        ],
        input_variables=["report", "question"],
        output_variables=["scoring", "feasibility", "approval"]
    )

    try:
        result = chain.invoke({"report": report_text, "question": question_content or "无额外题目要求"})
        # 解析评分 JSON
        try:
            scoring_data = json.loads(result["scoring"])
            result.update({
                "score": scoring_data.get("score", "N/A"),
                "compliance": scoring_data.get("compliance", "N/A"),
                "scoring_details": scoring_data.get("scoring_details", {})
            })
        except Exception:
            result["score"] = "解析失败"
            result["compliance"] = result["scoring"]
        return result

    except Exception as e:
        return {
            "score": "0",
            "compliance": f"AI处理失败：{e}",
            "feasibility": "无法评估",
            "approval": "审批过程中出现错误，请稍后重试。"
        }

def generate_markdown_report(result: Dict[str, str], file_path: str) -> str:
    """生成Markdown格式的评审报告"""
    filename = os.path.basename(file_path)
    current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    
    # 构建报告内容
    markdown = f"""# 实验报告评审报告

## 基本信息
- **评审文件**: {filename}
- **评审时间**: {current_time}
- **综合评分**: {result.get('score', 'N/A')}/100
- **合规性**: {result.get('compliance', 'N/A')}

## 详细评分
"""
    
    # 添加详细评分
    if "scoring_details" in result and isinstance(result["scoring_details"], dict):
        for category, detail in result["scoring_details"].items():
            markdown += f"- **{category}**: {detail}\n"
    else:
        markdown += "- 无详细评分信息\n"
    
    # 添加可行性评估
    markdown += f"""
## 可行性评估
{result.get('feasibility', 'N/A')}

## 最终审批意见
{result.get('approval', 'N/A')}

---
*本报告由DeepSeek AI实验报告自动评审系统生成*
"""
    
    return markdown

def save_markdown_report(markdown_content: str, file_path: str):
    """保存Markdown报告到文件"""
    # 确定保存路径
    base_name = os.path.splitext(file_path)[0]
    output_path = f"{base_name}_评审报告.md"
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return output_path

# ---------------------------
# 使用示例和测试
if __name__ == "__main__":
    # 测试文件路径 - 请修改为实际存在的文件路径
    test_file = "C:/Users/86150/Desktop/人工智能导论/实验3/人工智能导论-实验3-20221922-刘俊涛.docx"
    
    # 检查文件是否存在
    if os.path.exists(test_file):
        print(f"找到文件: {test_file}")
        result = approve_report_deepseek(test_file)
        
        print("\n" + "="*50)
        print(f"综合评分: {result.get('score', 'N/A')}")
        print(f"合规性: {result.get('compliance', 'N/A')}")
        
        print("\n" + "="*50)
        print("可行性评估:\n", result.get("feasibility", "N/A"))
        
        print("\n" + "="*50)
        print("审批意见:\n", result.get("approval", "N/A"))
        
        # 显示详细评分信息（如果存在）
        if "scoring_details" in result:
            print("\n" + "="*50)
            print("详细评分:")
            for category, detail in result["scoring_details"].items():
                print(f"{category}: {detail}")
        
        # 生成并保存Markdown报告
        markdown_report = generate_markdown_report(result, test_file)
        saved_path = save_markdown_report(markdown_report, test_file)
        print(f"\nMarkdown评审报告已保存至: {saved_path}")
                
    else:
        print(f"文件不存在: {test_file}")
        print("请检查文件路径是否正确")
        
        # 列出桌面目录帮助调试
        desktop_path = "C:/Users/86150/Desktop"
        if os.path.exists(desktop_path):
            print("\n桌面上的文件和文件夹：")
            for item in os.listdir(desktop_path)[:10]:  # 只显示前10个
                print(f"  - {item}")


