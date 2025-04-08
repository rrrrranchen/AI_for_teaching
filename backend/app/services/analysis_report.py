import json
import os
import uuid
import markdown
import pdfkit
from openai import OpenAI
from collections import Counter
from datetime import datetime

key = 'sk-b7550aa67ed840ffacb5ca051733802c'
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

def generate_study_report(json_data):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个教育数据分析专家，用户会输入一组学生的答题数据（格式为JSON数组），"
                    "请你生成一份**详细的学情分析报告**，内容包括：\n"
                    "- 总体表现统计（正确率、错误数）\n"
                    "- 错题分布和典型错误\n"
                    "- 学习建议\n"
                    "- 语言专业、有条理、使用 Markdown 格式\n"
                )
            },
            {
                "role": "user",
                "content": f"以下是学生的答题数据：\n{json.dumps(json_data, ensure_ascii=False)}"
            }
        ],
        stream=False
    )
    return response.choices[0].message.content.strip()


# 生成总体答题结果报告
def generate_study_report_overall(data):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个教育数据分析专家，用户会输入一组整个班级的答题数据，"
                    "请你生成一份**详细的学情分析报告**，内容包括：\n"
                    "- 总体表现统计（正确率、错误数）\n"
                    "- 错题分布和典型错误\n"
                    "- 学习建议\n"
                    "- 语言专业、有条理、使用 Markdown 格式\n"
                )
            },
            {
                "role": "user",
                "content": f"以下是学生的答题数据：\n{data}"
            }
        ],
        stream=False
    )
    return response.choices[0].message.content.strip()


def save_to_markdown(content, filename="答题结果分析报告.md"):
    """
    保存内容为 Markdown 文件，并确保文件名具有唯一性
    :param content: 要保存的内容
    :param filename: 文件名，默认为 "答题结果分析报告.md"
    :return: 保存的文件的相对路径
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_folder = os.path.join(project_root, 'static', 'analysis_report')
    
    # 确保目录存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 生成唯一的文件名
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(output_folder, unique_filename)
    
    # 写入内容到文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    # 返回以 'static' 开头的相对路径
    relative_path = os.path.join('static', 'analysis_report', unique_filename)
    print(f"\n✅ 学情分析报告已保存为 Markdown 文件：{relative_path}")
    return relative_path


def save_to_pdf(content, filename="答题结果分析报告.pdf"):
<<<<<<< HEAD
    # ========= 1. 构建 wkhtmltopdf.exe 路径 =========
    current_dir = os.path.dirname(__file__)
    wkhtmltopdf_path = os.path.abspath(
        os.path.join(current_dir, '..', 'tools', 'wkhtmltopdf', 'bin', 'wkhtmltopdf.exe')
    )
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

    # ========= 2. Markdown -> HTML =========
    html_content = markdown.markdown(content)
    html_template = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: "SimSun", serif; line-height: 1.6; margin: 40px; }}
            h1 {{ text-align: center; color: #2c3e50; }}
            h2 {{ color: #2c3e50; margin-top: 25px; }}
            .section {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h1>教案设计</h1>
        <div class="section">{html_content}</div>
    </body>
    </html>
    """

    # ========= 3. 构建输出路径 =========
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_folder = os.path.join(project_root, 'static', 'analysis_report')
    os.makedirs(output_folder, exist_ok=True)

    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(output_folder, unique_filename)

    # ========= 4. 写入 PDF =========
    pdfkit.from_string(html_template, filepath, configuration=config)

    # ========= 5. 打印并返回相对路径 =========
    relative_path = os.path.join('static', 'analysis_report', unique_filename)
    print(f"\n学情分析报告已保存为 PDF 文件：{relative_path}")
    return relative_path
=======
     # 将 Markdown 转换为 HTML
     html_content = markdown.markdown(content)

     # HTML 模板
     html_template = f"""
     <html>
     <head>
         <meta charset="utf-8">
         <style>
             body {{ font-family: "SimSun", serif; line-height: 1.6; margin: 40px; }}
             h1 {{ text-align: center; color: #2c3e50; }}
             h2 {{ color: #2c3e50; margin-top: 25px; }}
             .section {{ margin-bottom: 20px; }}
         </style>
     </head>
     <body>
         <h1>教案设计</h1>
         <div class="section">{html_content}</div>
     </body>
     </html>
     """

     # 手动指定 wkhtmltopdf 路径
     pdfkit_config = pdfkit.configuration(wkhtmltopdf=r"E:\Software\wkhtmltopdf\bin\wkhtmltopdf.exe")

     # 生成 PDF
     pdfkit.from_string(html_template, filename, configuration=pdfkit_config)
     print(f"\nPDF 已保存为：{filename}")
>>>>>>> 86e9fbdab3de7a9d2ea918f57a768e03b3405f0a


json_data = [
    {
        "id": 14,
        "question_id": 84,
        "class_id": 1,
        "answer": "C",
        "correct_percentage": 100,
        "question_content": "{\"question\": \"以下哪个协议用于网络层的错误报告和控制信息？\", \"options\": [\"A. TCP\", \"B. UDP\", \"C. ICMP\", \"D. IP\"]}",
        "correct_answer": "C",
        "course_name": "操作系统第一章"
    },
    {
        "id": 15,
        "question_id": 85,
        "class_id": 1,
        "answer": "A",
        "correct_percentage": 0,
        "question_content": "{\"question\": \"以下哪个设备用于连接不同网络段？\", \"options\": [\"A. 集线器\", \"B. 交换机\", \"C. 路由器\", \"D. 网桥\"]}",
        "correct_answer": "C",
        "course_name": "操作系统第一章"
    },
    {
        "id": 16,
        "question_id": 86,
        "class_id": 1,
        "answer": "B",
        "correct_percentage": 100,
        "question_content": "{\"question\": \"以下哪个协议用于文件传输？\", \"options\": [\"A. HTTP\", \"B. FTP\", \"C. SMTP\", \"D. Telnet\"]}",
        "correct_answer": "B",
        "course_name": "操作系统第一章"
    },
    {
        "id": 17,
        "question_id": 87,
        "class_id": 1,
        "answer": "C",
        "correct_percentage": 100,
        "question_content": "{\"question\": \"以下哪个协议用于邮件传输？\", \"options\": [\"A. HTTP\", \"B. FTP\", \"C. SMTP\", \"D. Telnet\"]}",
        "correct_answer": "C",
        "course_name": "操作系统第一章"
    },
    {
        "id": 18,
        "question_id": 88,
        "class_id": 1,
        "answer": "B",
        "correct_percentage": 100,
        "question_content": "{\"question\": \"以下哪个协议用于远程登录？\", \"options\": [\"A. HTTP\", \"B. Telnet\", \"C. FTP\", \"D. SNMP\"]}",
        "correct_answer": "B",
        "course_name": "操作系统第一章"
    },
    {
        "id": 19,
        "question_id": 89,
        "class_id": 1,
        "answer": "C",
        "correct_percentage": 100,
        "question_content": "{\"question\": \"以下哪个协议用于网络管理？\", \"options\": [\"A. HTTP\", \"B. FTP\", \"C. SNMP\", \"D. Telnet\"]}",
        "correct_answer": "C",
        "course_name": "操作系统第一章"
    },
    {
        "id": 20,
        "question_id": 90,
        "class_id": 1,
        "answer": "A",
        "correct_percentage": 0,
        "question_content": "{\"question\": \"以下哪个协议用于网页浏览？\", \"options\": [\"A. HTTP\", \"B. FTP\", \"C. Telnet\", \"D. SNMP\"]}",
        "correct_answer": "A",
        "course_name": "操作系统第一章"
    },
    {
        "id": 21,
        "question_id": 91,
        "class_id": 1,
        "answer": "D",
        "correct_percentage": 100,
        "question_content": "{\"question\": \"以下哪个设备用于隔离不同网络？\", \"options\": [\"A. 交换机\", \"B. 路由器\", \"C. 网桥\", \"D. 防火墙\"]}",
        "correct_answer": "D",
        "course_name": "操作系统第一章"
    },
    {
        "id": 22,
        "question_id": 92,
        "class_id": 1,
        "answer": "C",
        "correct_percentage": 100,
        "question_content": "{\"question\": \"以下哪个协议用于简单邮件访问？\", \"options\": [\"A. HTTP\", \"B. FTP\", \"C. POP3\", \"D. Telnet\"]}",
        "correct_answer": "C",
        "course_name": "操作系统第一章"
    },
    {
        "id": 23,
        "question_id": 93,
        "class_id": 1,
        "answer": "B",
        "correct_percentage": 0,
        "question_content": "{\"question\": \"以下哪个协议用于安全的网页浏览？\", \"options\": [\"A. HTTP\", \"B. HTTPS\", \"C. FTP\", \"D. Telnet\"]}",
        "correct_answer": "B",
        "course_name": "操作系统第一章"
    },
    {
        "id": 24,
        "question_id": 94,
        "class_id": 1,
        "answer": "A",
        "correct_percentage": 100,
        "question_content": "{\"question\": \"以下哪个协议用于域名解析？\", \"options\": [\"A. DNS\", \"B. HTTP\", \"C. FTP\", \"D. Telnet\"]}",
        "correct_answer": "A",
        "course_name": "操作系统第一章"
    }
]
