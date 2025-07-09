from openai import OpenAI

client = OpenAI(
    base_url="https://api.deepseek.com/",
    api_key="sk-ca9d2a314fda4f8983f61e292a858d17"
)

completion = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {
                "role": "system",
                "content": "你是一位大模型提示词生成专家，请根据用户的需求编写一个智能助手的提示词，来指导大模型进行内容生成，要求：\n1. 以 Markdown 格式输出\n2. 贴合用户需求，描述智能助手的定位、能力、知识储备\n3. 提示词应清晰、精确、易于理解，在保持质量的同时，尽可能简洁\n4. 只输出提示词，不要输出多余解释"
        },
        {
                "role": "user",
                "content": "请帮我生成一个“学生学习助手”的提示词"
        }
    ]
)

print(completion.choices[0].message.content)