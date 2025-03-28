# from sparkai.llm.llm import ChatSparkLLM
# from sparkai.core.messages import ChatMessage


# SPARKAI_URL = 'wss://spark-api.xf-yun.com/v4.0/chat'

# SPARKAI_APP_ID = 'fdc65b4b'
# SPARKAI_API_SECRET = 'ZDFmMzg5Yjk2ZTVhMmNhNjM2Nzc2ZmMz'
# SPARKAI_API_KEY = 'bd45dc727ac09175b09d3c2f5b2b993c'

# SPARKAI_DOMAIN = '4.0Ultra'

# def generate_lesson_plan(title, description):
#     return "教案示例"
    

#实现调用ai接口获取相关题目功能(参数)

from openai import OpenAI
import time
import json
# import pptx
from pptx import Presentation, util
from pptx.dml.color import RGBColor
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from typing import Optional, List, Any
from datetime import datetime


# 定义自己的 API Key
key = 'sk-b7550aa67ed840ffacb5ca051733802c'
api_url = "https://api.deepseek.com"  # DeepSeek 的 API 地址
# OpenAI 参数设置：API Key + API Interface (这里访问接口为 DeepSeek 的 API 地址)


# 逐字打印效果
def printChar(text, delay=0.1):
    for char in text:
        print(char, end='', flush=True)  # 使用 end='' 防止自动换行，flush=True 确保立即打印
        time.sleep(delay)
    print()  # 最后打印一个换行符


# 发送请求到 DeepSeek
def sendToDeepSeek(say):
    print('正在验证身份，请稍等....')
    # 请求接口并验证身份，创建客户端对象
    client = OpenAI(api_key=key, base_url=api_url)
    print('正在思考，请耐心等待...')
    # 发送请求数据并等待获取响应数据
    response = client.chat.completions.create(
        model="deepseek-chat",  # 使用的模型
        messages=[
            {"role": "system", "content": "你是一个专业的客服助手，请用正式的语气回答用户的问题。"},
            # {"role": "system", "content": "你是风趣幽默的客服，请用轻松幽默的语气回答用户的问题。"},
            {"role": "user", "content": say},
        ],
        stream=False  # 是否启用流式输出
    )
    # print(response)  # 如果需要调试，可以打印完整的响应
    return response.choices[0].message.content  # 返回模型生成的回复内容


# DeepSeek 问答环节
def callDeepSeek():
    # 主循环
    while True:
        myin = input('您请说：')  # 获取用户输入
        if myin == 'bye':  # 如果用户输入 "bye"，退出循环
            print('欢迎下次使用！再见！')
            break
        resp = sendToDeepSeek(myin)  # 发送用户输入到 DeepSeek 并获取回复
        printChar(resp)  # 逐字打印回复内容
        # print(resp)  # 如果需要直接打印完整回复，可以使用这行代码
        print('-----------------------------------------------------------')


# 测试接口
# callDeepSeek()


class DeepSeekLLM(LLM):
    def _call(self, prompt: str,
              stop: Optional[List[str]] = None,
              run_manager: Optional[CallbackManagerForLLMRun] = None,
              **kwargs: Any) -> str:
        # 调用 sendToDeepSeek 函数
        response = sendToDeepSeek(prompt)
        return response

    @property
    def _llm_type(self) -> str:
        return "deepseek"


# 获取 DeepSeek 生成的教学内容
def fetch_teaching_content(subject, chapter):
    # 使用自定义的 DeepSeek LLM
    llm = DeepSeekLLM()

    # 提取知识点
    template1 = """
    你是一位资深数学教师，请根据以下文本提取知识点：
    文本：{text}
    按JSON格式输出，包含字段：["subject", "chapter", "core_concept", "related_formulas", "difficult_points", "typical_examples"]
    """
    prompt1 = PromptTemplate(template=template1, input_variables=["text"])
    chain1 = LLMChain(llm=llm, prompt=prompt1)

    # 运行链并获取结果
    # knowledge = chain1.run("勾股定理：直角三角形斜边平方等于两直角边平方和，公式为a²+b²=c²")
    text1 = f"{subject}{chapter}"
    knowledge = chain1.invoke(text1)  # knowledge是包含json字符串的字典

    print(knowledge['text'])
    # if 'json' in knowledge['text']:
    #     knowledge['text'].replace('json', '')
    # if '`' in knowledge['text']:
    #     knowledge['text'].replace('`', '')
    if 'json' in knowledge['text']:
        knowledge['text'] = knowledge['text'].replace('json', '')
    while '`' in knowledge['text']:
        knowledge['text'] = knowledge['text'].replace('`', '')
    return knowledge['text']


# 创建PPT
def create_ppt(content, ppt_filename="教学示例PPt.pptx"):
    # 创建一个PPT演示文稿
    prs = Presentation()

    # 添加封面页
    slide_layout = prs.slide_layouts[0]  # 选择标题页布局
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = f"{content['subject']} - {content['chapter']}"
    subtitle.text = "教学内容概览"

    # 添加核心概念
    slide_layout = prs.slide_layouts[1]  # 选择标题和内容布局
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "核心概念"
    body = slide.shapes.placeholders[1].text_frame
    body.text = content['core_concept']

    # 添加相关公式
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "相关公式"
    body = slide.shapes.placeholders[1].text_frame
    # 逐个添加每个公式
    for formula in content['related_formulas']:
        p = body.add_paragraph()  # 添加一个新的段落
        p.text = formula  # 设置段落内容

    # 添加重难点
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "重难点"
    body = slide.shapes.placeholders[1].text_frame
    # 逐个添加每个重难点
    for point in content['difficult_points']:
        p = body.add_paragraph()  # 添加一个新的段落
        p.text = point  # 设置段落内容

    # 添加典型例题
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "典型例题"
    body = slide.shapes.placeholders[1].text_frame
    # 逐个添加每个例题
    for example in content['typical_examples']:
        p = body.add_paragraph()  # 添加一个新的段落
        p.text = example  # 设置段落内容

    # 保存PPT文件到本地
    prs.save(ppt_filename)
    print(f"PPT已保存为: {ppt_filename}")


# 生成PPT
# def generate_ppt(subject, chapter, ppt_filename=None):
#     try:
#         # 获取教学内容
#         content = fetch_teaching_content(subject, chapter)
#         print(content)
#         content = json.loads(content)
#         print(content)

#         # 创建PPT
#         if ppt_filename is None:
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             ppt_filename = f"ppts/{subject}-{chapter}教学PPT{timestamp}.pptx"
#         create_ppt(content, ppt_filename)
#     except Exception as e:
#         print(f"发生错误: {e}")


# 测试调用生成PPT（科目：数学，章节：勾股定理）
# subject = "数学"
# chapter = "勾股定理"

# generate_ppt(subject, chapter)


def set_text_font(shape, font_name='等线', font_size=16, font_color=RGBColor(255, 255, 255)):
    text_frame = shape.text_frame

    # 遍历所有段落和文本运行
    for paragraph in text_frame.paragraphs:
        for run in paragraph.runs:
            # 设置字体名称
            run.font.name = font_name
            # 设置字体大小（单位：磅）
            run.font.size = util.Pt(font_size)
            # 设置颜色
            run.font.color.rgb = font_color
            # 设置加黑
            # run.font.bold = False
            # 设置斜体
            # run.font.italic = False
            # -> 取默认


def keep_text_font(shape, new_text):  # -> 仅处理单个run -> 禁止多个run -> 反复添加text及各run字体属性
    text_frame = shape.text_frame

    for paragraph in text_frame.paragraphs:
        # 创建新 Run 并继承格式（取第一个 Run 的格式）
        if paragraph.runs:
            # 清空所有 Run 的文本
            for run in paragraph.runs:
                run.text = ""

            first_run = paragraph.runs[0]
            new_run = paragraph.add_run()
            new_run.text = new_text

            # 复制字体属性
            new_run.font.name = first_run.font.name
            new_run.font.size = first_run.font.size
            new_run.font.bold = first_run.font.bold
            new_run.font.italic = first_run.font.italic
            new_run.font.color.rgb = first_run.font.color.rgb


def set_content(content, teacher_name, time, title, template):
    """
    content = {
    '学科':
    '章节':
    '概念阐述':详细解释该知识点的核心概念，明确其定义，使学生理解其基本含义。
通过具体实例，展示概念在实际情境中的应用，加深学生对概念的理解。
    '思维导图':利用思维导图梳理核心概念的要点，帮助学生系统地掌握知识。
在思维导图中突出重点内容，便于学生快速回顾和记忆。
    '内涵扩展':深入剖析概念的内涵，探讨其在不同情况下的表现形式。
引导学生思考概念与其他相关概念的联系与区别，构建知识体系。
    '公式变形':介绍公式的常见变形形式，说明每种变形的适用条件。
通过具体例子，让学生熟悉公式变形后的应用，提高解题能力。
    '推导过程':详细展示公式的推导过程，每一步骤都清晰标注，便于学生理解。
在推导过程中，结合图形或图表辅助说明，使抽象的公式更直观。
    '公式记忆技巧':提供一些记忆公式的小技巧，帮助学生更好地记住公式。
强调公式中的关键部分，提醒学生在记忆时注意细节。
    '重点知识点':精准定位本章节的重点知识点，详细讲解其重要性和应用范围。
通过对比分析，让学生明白重点知识点与其他知识点的区别。
    '重点公式应用':重点讲解公式在实际问题中的应用，通过典型例题展示其解题思路。
强调公式应用时需要注意的细节，避免学生在解题过程中出现错误。
    '重点题型':总结本章节的重点题型，分析其解题方法和技巧。
提供一些变式题，让学生在练习中巩固对重点题型的理解。
    '突破方法':提供多种突破难点的方法，如类比法、图示法等，帮助学生理解。
引导学生从不同角度思考问题，培养他们的思维能力。
    '典型例题讲解':选取典型的难点例题，详细讲解解题过程，突出关键步骤。
在讲解过程中，引导学生总结解题规律，提高解题能力。
    '难点剖析':深入分析本章节的难点，找出学生容易出错的地方。
通过具体例子，让学生直观地理解难点的成因。
    '基础例题':{
        '例题展示':展示基础例题，涵盖本章节的主要知识点和公式。
通过逐步讲解，让学生掌握解题的基本方法和步骤。
        '解题思路':引导学生分析题目，找出解题的关键点。
总结解题思路，让学生在遇到类似题目时能够迅速找到解题方向。
        '答案解析':提供详细的答案解析，包括每一步的计算过程和依据。
强调答案的规范性，让学生养成良好的解题习惯。
    }
    '中等难度例题':{
        '答案核对':提供答案核对，让学生检查自己的解题过程是否正确。
对于错误的解题过程，分析原因，帮助学生避免类似错误。
        '解题方法':介绍多种解题方法，让学生在解题过程中灵活运用。
引导学生比较不同解题方法的优缺点，选择最适合自己的方法。
        '例题分析':选取中等难度的例题，增加题目的综合性。
分析题目中的知识点和公式应用，让学生学会综合运用所学知识。
    }
    '拓展提升例题':{
        '例题拓展':展示拓展提升例题，提高学生的思维能力和解题技巧。
通过拓展例题，引导学生将所学知识应用到更复杂的情境中。
        '方法总结':总结拓展提升例题的解题方法和技巧，让学生在解题过程中有所借鉴。
强调解题方法的通用性，让学生能够将所学方法应用到其他题目中。
        '思维训练':在解题过程中，注重对学生思维的训练，培养他们的创新思维。
引导学生从不同角度思考问题，寻找多种解题方法。
    }
    """
    prs = Presentation(template)

    content_pages = [3, 5, 7, 8, 10, 11, 12]
    # PPT shapes全为文本框，这里可以省去判断步骤
    for slide in prs.slides:
        # func = processions.get(prs.slides.index(slide), lambda _: print('查无此页！'))
        # func = processions.get(prs.slides.index(slide), lambda _: print(''))  # 默认不做处理
        # func(slide, ...) -> 不好设置传参
        idx = prs.slides.index(slide)
        if idx == 0:
            fill_main(slide, teacher_name, time, title)  # keep_font=True
        elif idx == 13:
            fill_main(slide, teacher_name, time)
        elif idx in content_pages:
            fill_content(slide, content)

    return prs


def fill_main(slide, name, time, title=None, keep_font=False):
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text:
            text = shape.text
            if text == '标题':
                if not keep_font:
                    shape.text = title
                    set_text_font(shape, '标准粗黑', 43)
                else:
                    keep_text_font(shape, title)
            if text == '姓名':
                if not keep_font:
                    shape.text = name
                    set_text_font(shape)
                else:
                    keep_text_font(shape, name)
            if text == '年月日.X':
                if not keep_font:
                    shape.text = time
                    set_text_font(shape)
                else:
                    keep_text_font(shape, time)


def fill_content(slide, content, keep_font=False):
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text:
            text = shape.text
            if '内容' in text:
                if not keep_font:
                    key = text.replace('内容', '')
                    shape.text = content[key]  # .get(key)
                    set_text_font(shape, font_color=RGBColor(0, 0, 0))
                else:
                    key = text.replace('内容', '')
                    new_text = content[key]
                    keep_text_font(shape, new_text)


