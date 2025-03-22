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

# 定义自己的 API Key
key = 'sk-b7550aa67ed840ffacb5ca051733802c'
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
    client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
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
def askDeepSeek():
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
# askDeepSeek()
    
