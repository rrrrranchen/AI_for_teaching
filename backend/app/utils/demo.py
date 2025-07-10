from openai import OpenAI

client = OpenAI(
    base_url="https://api.deepseek.com/",
    api_key="sk-ca9d2a314fda4f8983f61e292a858d17"
)

completion = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
                "role": "system",
                "content": ""
        },
        {
                "role": "user",
                "content": """

分类存放接口函数

接口函数分类见文件名所示
根据以上内容写出readme.md文件，给我原始的markdown代码，使用中文描述
                """
        }
    ]
)

print(completion.choices[0].message.content)