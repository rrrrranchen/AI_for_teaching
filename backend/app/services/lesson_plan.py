import json
import re
from openai import OpenAI
import time
from docx import Document
import markdown
import pdfkit
from sqlalchemy import and_
from typing import Any, List, Dict, Union

import json
from typing import Dict
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










# 第一轮：精准知识点提取提示词
extraction_prompt = """请严格遵循以下要求从教学内容中提取技术知识点：
1. 仅提取纯技术性内容
2. 排除所有教学步骤、时间安排、互动活动等教学法相关内容
3. 保持技术术语的精确性
4. 按内容层级结构组织知识点
5. 对复杂概念进行必要拆解

待处理内容：
"""

# 第二轮：结构化生成提示词
generation_prompt = """请生成满足以下要求的思维导图JSON：
1. 保持技术体系的完整逻辑结构
2. 层级深度不超过6级
3. 每个节点必须包含"name"字段
4. 技术细节放入节点"content"字段
5. 使用Markdown语法标记关键术语

待结构化知识点：
"""

def generate_knowledge_mind_map(lesson_content: str) -> Dict:
    """
    通过严格类型检查的多轮对话生成知识点思维导图
    
    参数：
        lesson_content: 教学内容文本（自动处理为字符串）
        
    返回：
        JSON格式的思维导图数据
    """
    lesson_content = str(lesson_content)
    
    try:
        # 第一阶段：知识点提取
        phase1_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是精准的知识提取引擎"},
                {"role": "user", "content": extraction_prompt + lesson_content}
            ],
            temperature=0.1
        )
        
        # 第二阶段：结构生成
        knowledge_data = phase1_response.choices[0].message.content
        
        phase2_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是知识图谱架构师"},
                {"role": "user", "content": generation_prompt + knowledge_data}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        raw_response = phase2_response.choices[0].message.content
        processed = preprocess_response(raw_response)
        return validate_structure(processed)
        
    except Exception as e:
        print(f"生成过程中发生错误: {str(e)}")
        return get_default_structure()

def preprocess_response(raw: Any) -> Dict:
    """响应数据标准化处理"""
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except:
            data = {"name": "解析失败", "children": []}
    else:
        data = raw

    # 结构修正逻辑
    if "name" not in data:
        return {
            "name": "知识体系",
            "children": [convert_node(k, v) for k, v in data.items()]
        }
    return data

def convert_node(key: str, value: Any) -> Dict:
    """递归转换键值对为节点"""
    node = {"name": key}
    if isinstance(value, dict):
        node["children"] = [convert_node(k, v) for k, v in value.items()]
    elif isinstance(value, list):
        node["children"] = [{"name": str(item)} for item in value]
    else:
        node["content"] = str(value)
    return node

def validate_structure(data: Dict) -> Dict:
    """验证并补全思维导图结构"""
    if not isinstance(data, dict):
        return get_default_structure()
    
    # 确保必填字段存在
    if "name" not in data:
        data["name"] = "知识体系"
    
    # 确保children是列表
    if "children" not in data:
        data["children"] = []
    elif not isinstance(data["children"], list):
        data["children"] = []
    
    return data

def get_default_structure() -> Dict:
    """返回安全的默认结构"""
    return {
        "name": "知识点思维导图",
        "children": []
    }

    
if __name__ == "__main__":
    # 示例教学设计内容
    lesson_plan_content = {"plan_content": "# TCP\u8fde\u63a5\u4e0e\u4e09\u6b21\u63e1\u624b\u534f\u8bae\u6559\u5b66\u8bbe\u8ba1\n\n## \u6559\u5b66\u76ee\u6807\n1. \u80fd\u591f\u51c6\u786e\u63cf\u8ff0TCP\u534f\u8bae\u7684\u7279\u70b9\u53ca\u5176\u4e0eUDP\u534f\u8bae\u7684\u533a\u522b\uff08\u7406\u89e3\u5c42\u9762\uff09\n2. \u80fd\u591f\u89e3\u91caTCP\u4e09\u6b21\u63e1\u624b\u7684\u8fc7\u7a0b\u53ca\u5176\u5fc5\u8981\u6027\uff08\u5e94\u7528\u5c42\u9762\uff09\n3. \u80fd\u591f\u7ed8\u5236TCP\u4e09\u6b21\u63e1\u624b\u7684\u65f6\u5e8f\u56fe\u5e76\u6807\u6ce8\u5173\u952e\u5b57\u6bb5\uff08\u6280\u80fd\u5c42\u9762\uff09\n4. \u80fd\u591f\u5206\u6790\u4e09\u6b21\u63e1\u624b\u5931\u8d25\u7684\u53ef\u80fd\u539f\u56e0\uff08\u5206\u6790\u5c42\u9762\uff09\n5. \u80fd\u591f\u5728\u6a21\u62df\u73af\u5883\u4e2d\u89c2\u5bdfTCP\u8fde\u63a5\u5efa\u7acb\u8fc7\u7a0b\uff08\u5b9e\u8df5\u5c42\u9762\uff09\n\n## \u6559\u5b66\u91cd\u96be\u70b9\n**\u91cd\u70b9\uff1a**\n- TCP\u4e09\u6b21\u63e1\u624b\u7684\u5177\u4f53\u8fc7\u7a0b\n- \u6bcf\u4e2a\u63e1\u624b\u62a5\u6587\u7684\u5173\u952e\u5b57\u6bb5\u53ca\u5176\u4f5c\u7528\n\n**\u96be\u70b9\uff1a**\n- SYN/ACK\u6807\u5fd7\u4f4d\u7684\u7406\u89e3\n- \u5e8f\u5217\u53f7\u548c\u786e\u8ba4\u53f7\u7684\u53d8\u5316\u89c4\u5f8b\n- \u534a\u8fde\u63a5\u72b6\u6001\u7684\u7406\u89e3\n\n**\u7a81\u7834\u7b56\u7565\uff1a**\n- \u4f7f\u7528\u7c7b\u6bd4\u6cd5\uff08\u5982\u6253\u7535\u8bdd\u8fc7\u7a0b\uff09\u89e3\u91ca\u4e09\u6b21\u63e1\u624b\n- \u901a\u8fc7\u52a8\u753b\u6f14\u793a\u5e8f\u5217\u53f7\u53d8\u5316\u8fc7\u7a0b\n- \u8bbe\u8ba1\u5206\u7ec4\u89d2\u8272\u626e\u6f14\u6d3b\u52a8\u6a21\u62df\u63e1\u624b\u8fc7\u7a0b\n- \u4f7f\u7528Wireshark\u6293\u5305\u5206\u6790\u771f\u5b9eTCP\u8fde\u63a5\n\n## \u6559\u5b66\u5185\u5bb9\n1. **TCP\u534f\u8bae\u57fa\u7840**\n   - \u9762\u5411\u8fde\u63a5\u7684\u7279\u6027\n   - \u53ef\u9760\u4f20\u8f93\u673a\u5236\n   - \u4e0eUDP\u7684\u5bf9\u6bd4\uff08\u57fa\u4e8e\u5b66\u751f\u9884\u4e60\u53cd\u9988\u5f3a\u5316\uff09\n\n2. **\u8fde\u63a5\u5efa\u7acb\u8fc7\u7a0b**\n   - \u4e09\u6b21\u63e1\u624b\u5fc5\u8981\u6027\n   - \u5404\u9636\u6bb5\u72b6\u6001\u53d8\u5316\n   - \u5173\u952e\u5b57\u6bb5\u89e3\u6790\uff08SYN\u3001ACK\u3001seq\u3001ack\uff09\n\n3. **\u5e38\u89c1\u95ee\u9898\u5206\u6790**\n   - \u63e1\u624b\u5931\u8d25\u573a\u666f\n   - SYN Flood\u653b\u51fb\u539f\u7406\n   - \u8fde\u63a5\u8d85\u65f6\u5904\u7406\n\n4. **\u5b9e\u8df5\u5e94\u7528**\n   - \u7f51\u7edc\u8bca\u65ad\u4e2d\u7684TCP\u8fde\u63a5\u5206\u6790\n   - \u6027\u80fd\u4f18\u5316\u8003\u8651\n\n## \u6559\u5b66\u65f6\u95f4\u5b89\u6392\uff0845\u5206\u949f\uff09\n| \u6559\u5b66\u73af\u8282 | \u65f6\u95f4\u5206\u914d |\n|---------|---------|\n| \u5bfc\u5165\u73af\u8282 | 5\u5206\u949f |\n| TCP\u534f\u8bae\u57fa\u7840\u8bb2\u89e3 | 8\u5206\u949f |\n| \u4e09\u6b21\u63e1\u624b\u539f\u7406\u8bb2\u89e3 | 10\u5206\u949f |\n| \u4e92\u52a8\u6d3b\u52a81\uff1a\u89d2\u8272\u626e\u6f14 | 7\u5206\u949f |\n| \u4e92\u52a8\u6d3b\u52a82\uff1aWireshark\u6f14\u793a | 8\u5206\u949f |\n| \u4e92\u52a8\u6d3b\u52a83\uff1a\u6545\u969c\u8bca\u65ad | 5\u5206\u949f |\n| \u5c0f\u7ed3\u4e0e\u4f5c\u4e1a\u5e03\u7f6e | 2\u5206\u949f |\n\n## \u6559\u5b66\u8fc7\u7a0b\n\n### 1. \u5bfc\u5165\u73af\u8282\uff085\u5206\u949f\uff09\n**\u65b9\u6cd5\uff1a** \u60c5\u5883\u5bfc\u5165+\u63d0\u95ee\u4e92\u52a8  \n**\u6d3b\u52a8\uff1a** \n- \u5c55\u793a\u7f51\u7edc\u901a\u4fe1\u573a\u666f\u56fe\u7247\uff08\u5982\u7f51\u9875\u52a0\u8f7d\u3001\u89c6\u9891\u901a\u8bdd\uff09\n- \u63d0\u95ee\uff1a\"\u5f53\u4f60\u5728\u6d4f\u89c8\u5668\u8f93\u5165\u7f51\u5740\u540e\uff0c\u8ba1\u7b97\u673a\u5982\u4f55\u4e0e\u670d\u52a1\u5668\u5efa\u7acb\u8fde\u63a5\uff1f\"\n- \u6839\u636e\u5b66\u751f\u9884\u4e60\u53cd\u9988\uff08\u9898\u76eeID29\u6b63\u786e\u73870%\uff09\uff0c\u5f3a\u8c03TCP/UDP\u533a\u522b\u7684\u91cd\u8981\u6027\n\n**\u6559\u5177\uff1a** \u7f51\u7edc\u901a\u4fe1\u573a\u666f\u56fe\u7247\u3001\u9884\u4e60\u7b54\u9898\u7edf\u8ba1\u56fe\u8868  \n**\u9884\u671f\u6210\u679c\uff1a** \u6fc0\u53d1\u5b66\u4e60\u5174\u8da3\uff0c\u660e\u786e\u5b66\u4e60\u76ee\u6807\n\n### 2. TCP\u534f\u8bae\u57fa\u7840\u8bb2\u89e3\uff088\u5206\u949f\uff09\n**\u65b9\u6cd5\uff1a** \u5bf9\u6bd4\u8bb2\u89e3+\u56fe\u793a\u6cd5  \n**\u5185\u5bb9\uff1a**\n- \u56de\u987eOSI\u6a21\u578b\uff08\u57fa\u4e8e\u9898\u76eeID28\u53cd\u9988\uff09\n- \u5bf9\u6bd4TCP\u4e0eUDP\u7279\u6027\u8868\u683c\uff08\u5f3a\u5316\u9898\u76eeID29\u5185\u5bb9\uff09\n- \u901a\u8fc7\u5feb\u9012\u5305\u88f9\u7c7b\u6bd4\u89e3\u91ca\u53ef\u9760\u4f20\u8f93\n\n**\u5b66\u751f\u884c\u4e3a\uff1a** \u8bb0\u5f55\u5173\u952e\u70b9\uff0c\u53c2\u4e0e\u7c7b\u6bd4\u8ba8\u8bba  \n**\u6559\u5177\uff1a** \u5bf9\u6bd4\u8868\u683c\u3001\u5feb\u9012\u7c7b\u6bd4\u52a8\u753b  \n**\u9884\u671f\u6210\u679c\uff1a** \u5efa\u7acbTCP\u57fa\u7840\u8ba4\u77e5\u6846\u67b6\n\n### 3. \u4e09\u6b21\u63e1\u624b\u539f\u7406\u8bb2\u89e3\uff0810\u5206\u949f\uff09\n**\u65b9\u6cd5\uff1a** \u5206\u6b65\u8bb2\u89e3+\u52a8\u753b\u6f14\u793a  \n**\u5185\u5bb9\uff1a**\n1. \u63e1\u624b\u5fc5\u8981\u6027\uff1a\u89e3\u51b3\u4fe1\u9053\u4e0d\u53ef\u9760\u95ee\u9898\n2. \u8be6\u7ec6\u6b65\u9aa4\uff1a\n   - \u7b2c\u4e00\u6b21\u63e1\u624b\uff1aSYN=1, seq=x\n   - \u7b2c\u4e8c\u6b21\u63e1\u624b\uff1aSYN=1, ACK=1, seq=y, ack=x+1\n   - \u7b2c\u4e09\u6b21\u63e1\u624b\uff1aACK=1, seq=x+1, ack=y+1\n3. \u72b6\u6001\u53d8\u5316\uff1aCLOSED \u2192 SYN_SENT \u2192 ESTABLISHED\n\n**\u6559\u5177\uff1a** \u52a8\u6001\u65f6\u5e8f\u56fe\u3001\u72b6\u6001\u8f6c\u6362\u56fe  \n**\u9884\u671f\u6210\u679c\uff1a** \u7406\u89e3\u63e1\u624b\u6d41\u7a0b\u53ca\u5b57\u6bb5\u542b\u4e49\n\n### 4. \u4e92\u52a8\u6d3b\u52a81\uff1a\u89d2\u8272\u626e\u6f14\uff087\u5206\u949f\uff09\n**\u4e92\u52a8\u5f62\u5f0f\uff1a** \u5c0f\u7ec4\u89d2\u8272\u626e\u6f14  \n**\u5b89\u6392\uff1a**\n- \u5c06\u5b66\u751f\u5206\u4e3a3\u7ec4\uff1a\u5ba2\u6237\u7aef\u3001\u670d\u52a1\u5668\u3001\u89c2\u5bdf\u5458\n- \u5ba2\u6237\u7aef\u7ec4\u6301\"SYN\"\u5361\u7247\uff0c\u670d\u52a1\u5668\u7ec4\u6301\"SYN+ACK\"\u5361\u7247\n- \u6a21\u62df\u4e09\u6b21\u63e1\u624b\u8fc7\u7a0b\uff0c\u89c2\u5bdf\u5458\u8bb0\u5f55\u5e8f\u5217\u53f7\u53d8\u5316\n- \u6559\u5e08\u6545\u610f\u5236\u9020\"\u63e1\u624b\u5931\u8d25\"\u573a\u666f\u4f9b\u5206\u6790\n\n**\u6559\u5177\uff1a** \u7279\u5236\u624b\u5361\uff08\u542b\u5b57\u6bb5\u4fe1\u606f\uff09\u3001\u8ba1\u65f6\u5668  \n**\u9884\u671f\u6210\u679c\uff1a** \u901a\u8fc7\u4f53\u9a8c\u52a0\u6df1\u6d41\u7a0b\u8bb0\u5fc6\n\n### 5. \u4e92\u52a8\u6d3b\u52a82\uff1aWireshark\u6f14\u793a\uff088\u5206\u949f\uff09\n**\u4e92\u52a8\u5f62\u5f0f\uff1a** \u5b9e\u65f6\u6f14\u793a+\u95ee\u7b54  \n**\u5b89\u6392\uff1a**\n- \u6559\u5e08\u73b0\u573a\u8bbf\u95ee\u7f51\u7ad9\uff0c\u6355\u83b7TCP\u63e1\u624b\u8fc7\u7a0b\n- \u5b66\u751f\u89c2\u5bdf\u5e76\u56de\u7b54\uff1a\n  - \u627e\u51fa\u4e09\u6b21\u63e1\u624b\u62a5\u6587\n  - \u8bc6\u522b\u5e8f\u5217\u53f7\u53d8\u5316\u89c4\u5f8b\n  - \u8ba1\u7b97\u63e1\u624b\u8017\u65f6\n- \u5206\u7ec4\u8ba8\u8bba\u5f02\u5e38\u62a5\u6587\u7279\u5f81\n\n**\u6559\u5177\uff1a** Wireshark\u8f6f\u4ef6\u3001\u9884\u8bbe\u7f51\u7edc\u73af\u5883  \n**\u9884\u671f\u6210\u679c\uff1a** \u5efa\u7acb\u7406\u8bba\u5230\u5b9e\u8df5\u7684\u8fde\u63a5\n\n### 6. \u4e92\u52a8\u6d3b\u52a83\uff1a\u6545\u969c\u8bca\u65ad\uff085\u5206\u949f\uff09\n**\u4e92\u52a8\u5f62\u5f0f\uff1a** \u6848\u4f8b\u5206\u6790+\u5c0f\u7ec4\u7ade\u8d5b  \n**\u5b89\u6392\uff1a**\n- \u63d0\u4f9b3\u4e2a\u63e1\u624b\u5931\u8d25\u6848\u4f8b\uff08\u57fa\u4e8e\u9898\u76eeID30\u76f8\u5173\u7f51\u7edc\u5c42\u95ee\u9898\uff09\n- \u5c0f\u7ec4\u8ba8\u8bba\u53ef\u80fd\u539f\u56e0\u53ca\u89e3\u51b3\u65b9\u6848\n- \u6700\u5feb\u6b63\u786e\u8bca\u65ad\u7684\u5c0f\u7ec4\u83b7\u5f97\u5956\u52b1\u5206\n\n**\u6559\u5177\uff1a** \u6848\u4f8b\u5361\u7247\u3001\u767d\u677f\u8bb0\u5f55  \n**\u9884\u671f\u6210\u679c\uff1a** \u57f9\u517b\u95ee\u9898\u89e3\u51b3\u80fd\u529b\n\n### 7. \u5c0f\u7ed3\u4e0e\u4f5c\u4e1a\u5e03\u7f6e\uff082\u5206\u949f\uff09\n**\u65b9\u6cd5\uff1a** \u601d\u7ef4\u5bfc\u56fe\u56de\u987e  \n**\u5185\u5bb9\uff1a**\n- \u7528\u601d\u7ef4\u5bfc\u56fe\u4e32\u8054\u5173\u952e\u77e5\u8bc6\u70b9\n- \u5f3a\u8c03TCP\u53ef\u9760\u6027\u7684\u5b9e\u73b0\u673a\u5236\n- \u9884\u544a\u4e0b\u8282\u8bfe\u5185\u5bb9\uff08\u56db\u6b21\u6325\u624b\uff09\n\n## \u8bfe\u540e\u4f5c\u4e1a\n**\u57fa\u7840\u9898\uff1a**\n1. \u7ed8\u5236\u4e09\u6b21\u63e1\u624b\u65f6\u5e8f\u56fe\uff0c\u6807\u6ce8\u5404\u5b57\u6bb5\u503c\uff08\u5982\u521d\u59cbseq=100\uff09\n2. \u9009\u62e9\u9898\uff1a\u7b2c\u4e8c\u6b21\u63e1\u624b\u65f6\uff0cack\u5b57\u6bb5\u7684\u503c\u5e94\u8be5\u662f\uff08\u57fa\u4e8e\u9898\u76eeID30\u98ce\u683c\uff09\n   A. x B. x+1 C. y D. y+1\n\n**\u62d3\u5c55\u9898\uff1a**\n1. \u7814\u7a76SYN Cookie\u673a\u5236\u5982\u4f55\u9632\u5fa1SYN Flood\u653b\u51fb\n2. \u4f7f\u7528\u7f51\u7edc\u547d\u4ee4\uff08\u5982telnet\uff09\u5efa\u7acbTCP\u8fde\u63a5\uff0c\u8bb0\u5f55\u63e1\u624b\u8fc7\u7a0b\n\n**\u5b9e\u8df5\u9898\uff08\u9009\u505a\uff09\uff1a**\n\u4f7f\u7528Wireshark\u6355\u83b7\u5fae\u4fe1\u767b\u5f55\u8fc7\u7a0b\u7684TCP\u8fde\u63a5\uff0c\u5206\u6790\u5176\u63e1\u624b\u7279\u5f81\n\n---\n\u672c\u6559\u6848\u9488\u5bf9\u5b66\u751f\u9884\u4e60\u53cd\u9988\u4e2d\u66b4\u9732\u7684TCP/UDP\u7406\u89e3\u8584\u5f31\u95ee\u9898\uff08\u9898\u76eeID29\u6b63\u786e\u73870%\uff09\uff0c\u901a\u8fc7\u591a\u5c42\u6b21\u4e92\u52a8\u8bbe\u8ba1\u5f3a\u5316\u6982\u5ff5\u7406\u89e3\u3002\u7279\u522b\u8bbe\u8ba1\u4e86\u4ece\u7406\u8bba\u5230\u5b9e\u8df5\u7684\u591a\u901a\u9053\u5b66\u4e60\u8def\u5f84\uff0c\u7ed3\u5408\u7f51\u7edc\u5c42\u8bbe\u5907\u77e5\u8bc6\uff08\u9898\u76eeID30\uff09\u8fdb\u884c\u7efc\u5408\u8bad\u7ec3\u3002\u6240\u6709\u4e92\u52a8\u73af\u8282\u5747\u914d\u5907\u53ef\u89c6\u5316\u5de5\u5177\u652f\u6301\uff0c\u786e\u4fdd\u62bd\u8c61\u6982\u5ff5\u7684\u5177\u8c61\u5316\u5448\u73b0\u3002", "analysis": "\u81ea\u52a8\u8bc4\u4f30\u5931\u8d25\uff0c\u4f7f\u7528\u9ed8\u8ba4\u63a8\u8350\u6307\u6570"}
    # 生成思维导图数据
    mind_map_data = generate_knowledge_mind_map(lesson_plan_content)

    # 打印生成的思维导图数据
    print(json.dumps(mind_map_data, ensure_ascii=False, indent=2))