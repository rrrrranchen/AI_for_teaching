from openai import OpenAI
import time
import markdown2
import pdfkit

# 设置 API Key 和 DeepSeek API 地址
key = 'sk-b7550aa67ed840ffacb5ca051733802c'  # ← 请替换为你自己的 Key
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")


# 逐字打印函数
def printChar(text, delay=0.05):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


# 生成预备知识检测题和问卷
def generate_pre_class_questions(course_content):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "你是教学设计专家，请根据教师提供的课程内容生成一份预备知识检测练习题和一份调查问卷，用于了解学生对相关内容的了解程度。"
            },
            {
                "role": "user",
                "content": f"课程内容如下：\n{course_content}"
            }
        ],
        stream=False
    )
    return response.choices[0].message.content

# 将习题和问卷生成word文档
from docx import Document
import markdown

def save_to_word(content, filename="output.docx"):
    # 解析 Markdown 为纯文本（去掉 #，但保留结构）
    md_lines = content.split("\n")

    # 创建 Word 文档
    doc = Document()

    for line in md_lines:
        if line.startswith("# "):  # 一级标题
            doc.add_heading(line[2:], level=1)
        elif line.startswith("## "):  # 二级标题
            doc.add_heading(line[3:], level=2)
        elif line.startswith("### "):  # 三级标题
            doc.add_heading(line[4:], level=3)
        else:
            doc.add_paragraph(line)

    # 保存 Word 文件
    doc.save(filename)
    print(f"\n✅ Word 文件已保存为：{filename}")


# 生成结构化教案（按六大模块分段）
def generate_lesson_plans(course_content, student_feedback):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是教学设计专家，请根据教师提供的课程内容和学生答题反馈，"
                    "设计三套教案（分别适用于掌握良好、一般、薄弱的学生群体），"
                    "每套教案请严格按照以下六个模块输出：\n\n"
                    "1. 教学目标\n"
                    "2. 教学重难点\n"
                    "3. 教学内容\n"
                    "4. 教学时间安排\n"
                    "5. 教学过程\n"
                    "6. 课后作业"
                )
            },
            {
                "role": "user",
                "content": f"课程内容如下：\n{course_content}\n\n学生反馈如下：\n{student_feedback}"
            }
        ],
        stream=False
    )
    return response.choices[0].message.content

# 教案保存
def save_to_markdown(content, filename="教案.md"):
    """保存教案为 Markdown 文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅ 教案已保存为 Markdown 文件：{filename}")

# 教案保存为PDF
import pdfkit

def save_to_pdf(content, filename="教案.pdf"):
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
        <h1>📘 教案设计</h1>
        <div class="section">{html_content}</div>
    </body>
    </html>
    """

    # ✅ 手动指定 wkhtmltopdf 路径（仅 Windows 需要）
    pdfkit_config = pdfkit.configuration(wkhtmltopdf=r"E:\Software\wkhtmltopdf\bin\wkhtmltopdf.exe")

    # 生成 PDF
    pdfkit.from_string(html_template, filename, configuration=pdfkit_config)
    print(f"\n✅ PDF 已保存为：{filename}")



# 主程序
def teacher_assistant():
    print("🎓 欢迎使用【教师备课助手】\n")

    # 1. 输入课程内容
    course_content = input("📚 请输入本节课的教学内容（课程重点、教学目标等）：\n")

    print("\n🤖 正在生成预备知识检测题与学生问卷，请稍候...\n")
    # 生成习题和问卷
    questions = generate_pre_class_questions(course_content)
    print("✅ 以下是为本节课自动生成的内容：\n")
    printChar(questions)
    # 是否保存习题到 Word
    save_q = input("\n💾 是否将习题和问卷保存为 Word？(y/n): ")
    if save_q.lower() == 'y':
        save_to_word(questions, "预备知识检测题和问卷.docx")

    # 2. 输入学生答题情况
    student_feedback = input("\n📊 请输入学生答题结果、共性问题或学习反馈（可简述）：\n")

    print("\n🤖 正在根据反馈生成个性化教案，请稍候...\n")
    lesson_plans = generate_lesson_plans(course_content, student_feedback)
    print("📘 以下是结构化教案设计方案：\n")
    printChar(lesson_plans)

    save_to_markdown(lesson_plans)

    # 3. 是否保存为 PDF
    save = input("\n💾 是否将教案保存为 PDF？(y/n): ")
    if save.lower() == 'y':
        save_to_pdf(lesson_plans)

    print("\n🎉 教学设计完成，祝你上课顺利！")


# 启动程序
if __name__ == '__main__':
    teacher_assistant()
