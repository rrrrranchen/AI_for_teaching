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
from pptx import Presentation
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
def generate_ppt(subject, chapter, ppt_filename=None):
    try:
        # 获取教学内容
        content = fetch_teaching_content(subject, chapter)
        print(content)
        content = json.loads(content)
        print(content)

        # 创建PPT
        if ppt_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ppt_filename = f"ppts/{subject}-{chapter}教学PPT{timestamp}.pptx"
        create_ppt(content, ppt_filename)
    except Exception as e:
        print(f"发生错误: {e}")


# 测试调用生成PPT（科目：数学，章节：勾股定理）
# subject = "数学"
# chapter = "勾股定理"

# generate_ppt(subject, chapter)

