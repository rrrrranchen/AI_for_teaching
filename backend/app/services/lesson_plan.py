import json
from openai import OpenAI
import time
from docx import Document
import markdown
import pdfkit
from sqlalchemy import and_

from app.models.question import Question
from app.models.studentanswer import StudentAnswer

# 设置 API Key 和 DeepSeek API 地址
key = 'sk-b7550aa67ed840ffacb5ca051733802c'
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")


# 逐字打印函数
def printChar(text, delay=0.05):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


# 生成预备知识检测题和问卷
def generate_pre_class_questions(course_content):
    """
    调用AI接口生成课前预习题目，返回符合Question数据模型的题目列表
    :param course_content: 课程内容文本
    :param course_id: 关联的课程ID
    :return: 包含题目字典的列表，每个字典符合Question模型结构
    """
    # 构造更详细的系统提示，要求AI返回特定格式的题目
    system_prompt = """你是教学设计专家，请根据教师提供的课程内容生成3-5道预备知识检测练习题。
要求：
1. 返回格式为JSON列表，每个题目包含以下字段：
   - type: 题目类型(choice/fill/short_answer)
   - content: 题目内容
   - correct_answer: 正确答案
   - difficulty: 难度等级(1-5)
2. 题目类型要多样，包含选择题、填空题和简答题
3. 题目要真正检测学生对预备知识的掌握程度
4. 生成的选择题的题目内容中要包含选项，选择题正确答案应该是ABCD这样的形式"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"请为以下课程内容生成课前预习题目:\n{course_content}\n\n请返回符合要求的JSON格式题目列表。"
                }
            ],
            response_format={"type": "json_object"},  # 要求返回JSON格式
            stream=False
        )
        
        # 解析AI返回的JSON内容
        ai_response = json.loads(response.choices[0].message.content)
        
        # 确保返回的是列表格式
        questions_data = ai_response.get('questions', []) if isinstance(ai_response, dict) else ai_response
        
        # 转换为符合Question模型的格式
        questions = []
        for i, q in enumerate(questions_data, start=1):
            question = {
                "type": q.get("type", "choice"),  # 默认选择题
                "content": q.get("content", f"课前预习题目{i}"),
                "correct_answer": q.get("correct_answer", ""),
                "difficulty": min(max(int(q.get("difficulty", 3)), 1), 5),  # 确保难度在1-5范围内
                "timing": "pre_class"
            }
            questions.append(question)
        
        return questions
    
    except Exception as e:
        print(f"生成题目时出错: {e}")
        # 返回一个默认题目以防出错
        return [{
            "type": "choice",
            "content": f"关于{course_content[:50]}...的基本概念是什么？",
            "correct_answer": "默认正确答案",
            "difficulty": 3,
            "timing": "pre_class"
        }]
    



# 将习题和问卷生成word文档

# def save_to_word(content, filename="output.docx"):
#     # 解析 Markdown 为纯文本（去掉 #，但保留结构）
#     md_lines = content.split("\n")
#
#     # 创建 Word 文档
#     doc = Document()
#
#     for line in md_lines:
#         if line.startswith("# "):  # 一级标题
#             doc.add_heading(line[2:], level=1)
#         elif line.startswith("## "):  # 二级标题
#             doc.add_heading(line[3:], level=2)
#         elif line.startswith("### "):  # 三级标题
#             doc.add_heading(line[4:], level=3)
#         else:
#             doc.add_paragraph(line)
#
#     # 保存 Word 文件
#     doc.save(filename)
#     print(f"\n✅ Word 文件已保存为：{filename}")



# 生成结构化教案（按六大模块分段）
def generate_lesson_plans(course_content, student_feedback, student_level):
    """
    根据学生反馈和群体水平，生成一个教学方案
    :param course_content: 课程内容
    :param student_feedback: 学生反馈
    :param student_level: 学生群体水平（如 '良好', '一般', '薄弱'）
    :return: 教案内容
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{
            "role": "system",
            "content": (
                "你是教学设计专家，请根据教师提供的课程内容和学生答题反馈，"
                f"尽可能详细地设计适用于{student_level}群体的教案。\n\n"
                "每套教案请严格按照以下六个模块详细展开，并满足以下要求：\n\n"
                "1. 教学目标：明确列出3-5个可衡量的学习目标。\n"
                "2. 教学重难点：说明本节课的重点与难点，并简述突破策略。\n"
                "3. 教学内容：详细展开教学内容的结构，包括知识点的层次划分与逻辑关系。\n"
                "4. 教学时间安排：请按总课时45分钟，分配每一阶段的时间（含每个活动的分钟数）。\n"
                "5. 教学过程：\n"
                "    - 请按照“导入、讲授、互动、小结”顺序编排。\n"
                "    - 必须设计不少于三个互动环节，如小组讨论、角色扮演、实时问答、投票、课堂游戏等，同时在生成教学设计方案的时候要明确指出哪部分是互动环节。\n"
                "    - 每个环节说明教学方法、活动安排、教师与学生的行为、时间分配、使用的工具与材料、预期学习成果。\n"
                "6. 课后作业：布置有层次的作业任务，至少包含基础题与拓展题。\n\n"
                "请使用 Markdown 格式输出，便于后续整理归档，但不需要将内容加上markdown注释。每份教案的字数不得少于1000字。"
            )
        },
        {
            "role": "user",
            "content": f"课程内容如下：\n{course_content}\n\n学生反馈如下：\n{student_feedback}"
        }],
        stream=False
    )
    return response.choices[0].message.content



# 推荐指数
def evaluate_recommendation(student_feedback):
    """
    使用AI分析学生反馈，智能评估三套教案的适用性，返回推荐指数。
    推荐指数采用百分制。
    """
    # 构造AI提示
    system_prompt = """你是一个教学评估专家，请根据学生课前预习的答题反馈，评估三种教学方案的适用性。
要求：
1. 分析学生整体掌握情况
2. 给出三种教学方案(掌握良好/一般/薄弱)的推荐指数(百分制)
3. 返回格式为JSON，包含:
   - analysis: 简要分析
   - recommendation: 三种方案的推荐指数
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"请分析以下学生预习答题反馈:\n{student_feedback}\n\n请返回JSON格式的评估结果。"
                }
            ],
            response_format={"type": "json_object"},
            stream=False
        )
        
        # 解析AI返回的JSON内容
        ai_response = json.loads(response.choices[0].message.content)
        
        # 提取推荐指数
        recommendation = ai_response.get('recommendation', {
            '掌握良好': 33, 
            '掌握一般': 34, 
            '掌握薄弱': 33
        })
        
        # 确保所有值都存在且总和约等于100
        total = sum(recommendation.values())
        if total != 100:
            for key in recommendation:
                recommendation[key] = int(recommendation[key] / total * 100)
        
        # 添加分析说明
        recommendation['analysis'] = ai_response.get('analysis', 'AI分析完成')
        
        return recommendation
    
    except Exception as e:
        print(f"AI评估出错: {e}")
        # 出错时返回默认值
        return {
            '掌握良好': 33,
            '掌握一般': 34,
            '掌握薄弱': 33,
            'analysis': '自动评估失败，使用默认推荐指数'
        }


# 教案保存
def save_to_markdown(content, filename="教案.md"):
    """保存教案为 Markdown 文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅ 教案已保存为 Markdown 文件：{filename}")


# 教案保存为PDF
# def save_to_pdf(content, filename="教案.pdf"):
#     # 将 Markdown 转换为 HTML
#     html_content = markdown.markdown(content)
#
#     # HTML 模板
#     html_template = f"""
#     <html>
#     <head>
#         <meta charset="utf-8">
#         <style>
#             body {{ font-family: "SimSun", serif; line-height: 1.6; margin: 40px; }}
#             h1 {{ text-align: center; color: #2c3e50; }}
#             h2 {{ color: #2c3e50; margin-top: 25px; }}
#             .section {{ margin-bottom: 20px; }}
#         </style>
#     </head>
#     <body>
#         <h1>教案设计</h1>
#         <div class="section">{html_content}</div>
#     </body>
#     </html>
#     """
#
#     # 手动指定 wkhtmltopdf 路径
#     pdfkit_config = pdfkit.configuration(wkhtmltopdf=r"E:\Software\wkhtmltopdf\bin\wkhtmltopdf.exe")
#
#     # 生成 PDF
#     pdfkit.from_string(html_template, filename, configuration=pdfkit_config)
#     print(f"\n✅ PDF 已保存为：{filename}")


# 推荐指数
def evaluate_recommendation(student_feedback):
    """
    评估教学方案推荐指数
    :param student_feedback: 学生反馈
    :return: 包含推荐指数和分析的字典
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是教学评估专家..."},
                {"role": "user", "content": f"分析以下学生反馈:\n{student_feedback}"}
            ],
            response_format={"type": "json_object"},
            stream=False
        )
        
        ai_response = json.loads(response.choices[0].message.content)
        recommendation = ai_response.get('recommendation', {
            '掌握良好': 33, '掌握一般': 34, '掌握薄弱': 33
        })
        
        # 标准化百分比
        total = sum(recommendation.values())
        if total != 100:
            recommendation = {k: int(v/total*100) for k, v in recommendation.items()}
        
        return {
            **recommendation,
            'analysis': ai_response.get('analysis', 'AI分析完成')
        }
    
    except Exception:
        return {
            '掌握良好': 33,
            '掌握一般': 34,
            '掌握薄弱': 33,
            'analysis': '自动评估失败'
        }






# 主程序
def generate_teaching_plans(course_content, student_feedback):
    """
    主函数：生成三份教学设计方案
    :param course_content: 课程内容
    :param student_feedback: 学生反馈
    :return: 包含三份教案和推荐指数的字典列表
    """
    student_levels = ['掌握良好', '掌握一般', '掌握薄弱']
    recommendation_scores = evaluate_recommendation(student_feedback)
    
    lesson_plans = []
    for level in student_levels:
        content = generate_lesson_plans(course_content, student_feedback, level)
        lesson_plans.append({
            'level': level,
            'content': content,
            'recommendation': recommendation_scores.get(level, 0),
            'analysis': recommendation_scores.get('analysis', '')
        })
    
    return {
        'plans': lesson_plans,
        'recommendation': recommendation_scores
    }


