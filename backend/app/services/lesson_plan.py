import json
from openai import OpenAI
import time
from docx import Document
import markdown
import pdfkit
from sqlalchemy import and_
from typing import List, Dict, Union
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
import json


def generate_pre_class_questions(course_content: str) -> List[Dict[str, Union[str, int]]]:
    """
    生成课前预习题目（完整优化版）
    
    参数:
        course_content: 课程内容文本
        
    返回:
        题目列表，每个题目包含:
        - type: 题目类型 (choice/fill/short_answer)
        - content: 题目内容（选择题为JSON字符串）
        - correct_answer: 正确答案
        - difficulty: 难度等级 (1-5)
        - timing: 题目时间类型
        
    异常处理:
        - 自动修复格式问题
        - 提供默认值保证始终返回有效数据
    """
    system_prompt = """你是教学设计专家，请根据课程内容生成3-5道预备知识检测题。要求：
1. 返回JSON格式，包含questions数组
2. 每个题目包含:
   - type: 题目类型(choice/fill/short_answer)
   - content: 题目内容（选择题需包含question和options字段）
   - correct_answer: 正确答案
   - difficulty: 难度(1-5)
3. 选择题示例格式:
   {
     "type": "choice",
     "content": {
       "question": "问题文本",
       "options": ["A.选项1", "B.选项2"]
     },
     "correct_answer": "A"
   }
4. 用中文回答"""

    try:
        # 调用AI接口
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"课程内容:\n{course_content}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # 解析响应
        ai_data = json.loads(response.choices[0].message.content)
        raw_questions = ai_data.get("questions", [])
        
        processed_questions = []
        for i, q in enumerate(raw_questions, 1):
            question = {
                "type": validate_question_type(q.get("type")),
                "difficulty": clamp_difficulty(q.get("difficulty", 3)),
                "timing": "pre_class"
            }
            
            # 处理题目内容
            if question["type"] == "choice":
                content_data = parse_choice_content(q)
                question["content"] = json.dumps(content_data, ensure_ascii=False)
                question["correct_answer"] = validate_answer(
                    q.get("correct_answer"), 
                    content_data["options"]
                )
            else:
                question["content"] = str(q.get("content", f"问题{i}"))[:1000]
                question["correct_answer"] = str(q.get("correct_answer", ""))[:500]
            
            processed_questions.append(question)
        
        return processed_questions or [get_default_question(course_content)]

    except Exception as e:
        print(f"题目生成失败: {str(e)}")
        return [get_default_question(course_content)]

# 辅助函数 --------------------------------------------------

def validate_question_type(q_type: str) -> str:
    """验证题目类型"""
    valid_types = {"choice", "fill", "short_answer"}
    return q_type.lower() if q_type.lower() in valid_types else "choice"

def clamp_difficulty(diff: Union[int, float]) -> int:
    """限制难度范围1-5"""
    try:
        return max(1, min(5, int(diff)))
    except (TypeError, ValueError):
        return 3

def parse_choice_content(question_data: Dict) -> Dict:
    """解析选择题内容"""
    content = question_data.get("content", {})
    
    # 处理嵌套格式
    if isinstance(content, dict):
        question = content.get("question", "选择题")
        options = content.get("options", [])
    else:
        question = str(content)
        options = question_data.get("options", [])
    
    # 标准化选项
    if not isinstance(options, list):
        options = []
    
    # 确保每个选项有编号
    formatted_options = []
    for i, opt in enumerate(options[:10]):  # 最多10个选项
        opt_str = str(opt)
        if not opt_str.startswith(("A.", "B.", "C.", "D.", "E.", "F.")):
            prefix = chr(65 + i) + "."  # A., B., etc.
            opt_str = f"{prefix} {opt_str}"
        formatted_options.append(opt_str[:200])  # 限制选项长度
    
    # 确保至少2个选项
    if len(formatted_options) < 2:
        formatted_options = ["A. 选项A", "B. 选项B"]
    
    return {
        "question": str(question)[:500],
        "options": formatted_options
    }

def validate_answer(answer: str, options: List[str]) -> str:
    """验证选择题答案"""
    if not options:
        return "A"
    
    # 提取有效选项字母
    valid_choices = [opt[0] for opt in options if len(opt) > 0]
    if not valid_choices:
        return "A"
    
    # 处理答案格式
    answer_str = str(answer).strip().upper()
    if len(answer_str) > 0 and answer_str[0] in valid_choices:
        return answer_str[0]
    return valid_choices[0]  # 默认返回第一个选项

def get_default_question(course_content: str) -> Dict:
    """生成默认问题（备用）"""
    return {
        "type": "choice",
        "content": json.dumps({
            "question": f"关于{course_content[:50]}...的基本概念是什么？",
            "options": ["A. 基础概念", "B. 进阶内容", "C. 其他"]
        }, ensure_ascii=False),
        "correct_answer": "A",
        "difficulty": 3,
        "timing": "pre_class"
    }
    



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
                "3. 教学内容：详细展开教学内容的结构，包括知识点的层次划分与逻辑关系。同时，使用 Mermaid 标记语言生成结构化的教学内容结构图表。\n"
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


def generate_post_class_questions(lesson_plan_content: str) -> list:
    """
    调用 AI 接口根据教案内容生成课后习题，返回符合 Question 数据模型的题目列表
    :param lesson_plan_content: 教案内容文本
    :return: 包含题目字典的列表，每个字典符合 Question 模型结构
    """
    # 构造系统提示：要求生成检测学生对教案中知识点理解与掌握情况的课后习题
    system_prompt = """你是教学设计专家，请根据下面提供的教案内容生成15道课后巩固练习题。
要求：
1. 返回格式为JSON列表，每个题目包含以下字段：
   - type: 题目类型(choice/fill/short_answer)
   - content: 题目内容（选择题需包含question和options字段）
   - correct_answer: 正确答案
   - difficulty: 难度等级(1-5)
2. 题目类型要多样，包含选择题、填空题和简答题
3. 题目应检测学生对教案中涉及的关键知识点、互动环节以及实践环节的理解与掌握情况
4. 对于选择题，题目内容中应包含选项，并且正确答案格式为ABCD这样的形式
5. 选择题示例格式:
   {
     "type": "choice",
     "content": {
       "question": "问题文本",
       "options": ["A.选项1", "B.选项2"]
     },
     "correct_answer": "A"
   }
6. 用中文回答
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
                    "content": f"请根据下面的教案内容生成课后习题:\n{lesson_plan_content}\n\n请返回符合要求的JSON格式题目列表。"
                }
            ],
            response_format={"type": "json_object"},
            stream=False
        )

        # 解析 AI 返回的 JSON 内容
        ai_response = json.loads(response.choices[0].message.content)
        # 如果返回结果为字典且包含 'questions' 键，则取出对应列表，否则直接作为列表使用
        questions_data = ai_response.get('questions', []) if isinstance(ai_response, dict) else ai_response

        # 转换为符合 Question 模型格式（与课前习题格式保持一致）
        questions = []
        for i, q in enumerate(questions_data, start=1):
            question = {
                "type": q.get("type", "choice"),  # 默认题型为选择题
                "difficulty": min(max(int(q.get("difficulty", 3)), 1), 5),  # 难度限定在 1-5 之间
                "timing": "post_class"  # 标记为课后习题
            }

            if question["type"] == "choice":
                # 如果是选择题，content字段存储题目和选项的JSON格式
                content_data = q.get("content", {})
                if isinstance(content_data, dict):
                    question["content"] = json.dumps({
                        "question": content_data.get("question", f"课后习题{i}"),
                        "options": content_data.get("options", ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"])
                    }, ensure_ascii=False)
                else:
                    question["content"] = json.dumps({
                        "question": str(content_data),
                        "options": q.get("options", ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"])
                    }, ensure_ascii=False)
                question["correct_answer"] = q.get("correct_answer", "A")
            else:
                # 其他题型直接存储题目内容
                question["content"] = q.get("content", f"课后习题{i}")
                question["correct_answer"] = q.get("correct_answer", "")

            questions.append(question)

        return questions

    except Exception as e:
        print(f"生成课后习题时出错: {e}")
        # 出错时返回一个默认的课后习题，确保格式一致
        return [{
            "type": "choice",
            "content": json.dumps({
                "question": f"根据教案内容，回答关键知识点是什么？",
                "options": ["A. 基础概念", "B. 进阶内容", "C. 其他"]
            }, ensure_ascii=False),
            "correct_answer": "A",
            "difficulty": 3,
            "timing": "post_class"
        }]


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
        if not isinstance(recommendation, dict):
            raise ValueError("recommendation 不是字典类型")
        
        # 确保所有值都是数字
        for key, value in recommendation.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"recommendation 中的值 {key} 不是数字类型")
        
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
