import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from app.config import Config
import json

# 设置 API Key
key = Config.DEEPSEEK_API_KEY
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")


# 提取关键词的函数
def extract_keywords_from_design(report):
    # 使用 DeepSeek 进行关键词提取
    prompt = f"""
请从以下教学设计中提取出相关的一个关键词，要求：
- 关键词应紧密相关于课程内容。
- 只需一个关键词并且尽量简洁，最好不超过10个字。
- 例如：路由器与交换机区别、HTTPS 协议，而不是模糊的错误类型如“网络设备混淆”。


以下是设计内容：
{report}
"""
    # 调用 DeepSeek API 提取关键词
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个教育领域的助手，擅长从教学设计中提取关键点和关键词"},
            {"role": "user", "content": prompt}
        ],
        stream=False
    )

    # 返回提取的关键词
    extracted_keywords = response.choices[0].message.content.strip()
    return extracted_keywords

def extract_keywords_from_report(report):
    # 使用 DeepSeek 进行关键词提取
    prompt = f"""
请从以下报告中提取出 相关的一个具体知识点，要求：
- 知识点应紧密相关于课程内容，具体到学科概念或技能点。
- 只需一个知识点并且尽量简洁，最好不超过10个字。
- 重点关注学生常见错误的知识点，并排除泛泛的错误分类。
- 例如：路由器与交换机区别、HTTPS 协议理解，而不是模糊的错误类型如“网络设备混淆”。
- 知识点前加入课程名称。


以下是报告内容：
{report}
"""
    # 调用 DeepSeek API 提取关键词
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个教育领域的助手，擅长从学情报告中提取关键点和关键词"},
            {"role": "user", "content": prompt}
        ],
        stream=False
    )

    # 返回提取的关键词
    extracted_keywords = response.choices[0].message.content.strip()
    return extracted_keywords
# --------------------------------推荐视频----------------------------------------------
# 步骤1：抓取 B站视频链接
def recommend_bilibili_videos(keyword):
    search_url = f'https://search.bilibili.com/all?keyword={keyword}&from_source=nav_search'
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return f"❌ 无法获取搜索结果：{e}"

    soup = BeautifulSoup(response.text, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('//www.bilibili.com/video/') and 'BV' in href:
            full_link = 'https:' + href.split('?')[0]
            if full_link not in links:
                links.append(full_link)
        if len(links) >= 5:
            break
    return links


# 步骤2：抓取每个视频的原始标题 & 简介
def fetch_video_info(link):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(link, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.title.string.replace('_哔哩哔哩_bilibili', '').strip()
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        description = desc_tag['content'].strip() if desc_tag else '暂无简介'
        return {"title": title, "description": description, "link": link}
    except Exception as e:
        return {"title": "获取失败", "description": f"❌ 获取失败：{e}", "link": link}


# 步骤3：发送标题 & 简介给 AI，让它润色，不输出链接
def polish_title_description(video_infos):
    content_blocks = [
        f"原始标题：{info['title']}\n原始简介：{info['description']}"
        for info in video_infos
    ]
    content = "\n\n".join(content_blocks)

    prompt = f"""
请你对以下 Bilibili 视频的标题和简介进行语言润色，使其更正式、清晰、有教学感。
请注意：
- 不要添加视频链接
- 不要改变原始视频顺序
- 每条输出格式如下：
  - 资源推荐：润色后的标题
  - 资源简介：润色后的简介

以下是原始内容：
{content}
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一个教育内容润色助手，擅长规范化表达标题和简介"},
            {"role": "user", "content": prompt}
        ],
        stream=False
    )

    return response.choices[0].message.content.strip()


# 步骤4：主调用函数，组装最终 Markdown 格式输出
def generate_final_markdown(input):
    keyword = extract_keywords_from_design(input)
    links = recommend_bilibili_videos(keyword)
    if isinstance(links, str):
        return links  # 错误信息

    video_infos = [fetch_video_info(link) for link in links]
    ai_result = polish_title_description(video_infos)

    # 拆分 AI 输出，逐条绑定原始链接
    result_blocks = ai_result.strip().split("\n\n")
    markdown = []

    for i, block in enumerate(result_blocks):
        if i >= len(video_infos):
            break
        link = video_infos[i]["link"]
        markdown.append(f"{block.strip()}\n- 相关链接：{link}\n")

    return "\n".join(markdown)
# Modified version to return JSON format for video recommendations
def generate_final_json(input):
    keyword = extract_keywords_from_design(input)
    links = recommend_bilibili_videos(keyword)
    if isinstance(links, str):
        return json.dumps({"error": links}, ensure_ascii=False)  # Return error as JSON

    video_infos = [fetch_video_info(link) for link in links]
    ai_result = polish_title_description(video_infos)

    # Parse AI's polished results
    result_blocks = ai_result.strip().split("\n\n")
    videos = []
    
    for i, block in enumerate(result_blocks):
        if i >= len(video_infos):
            break
            
        # Parse the polished title and description
        lines = block.split('\n')
        polished_title = lines[0].replace("资源推荐：", "").strip()
        polished_desc = lines[1].replace("资源简介：", "").strip()
        
        videos.append({
            "title": polished_title,
            "description": polished_desc,
            "link": video_infos[i]["link"]
        })

    return json.dumps({"videos": videos}, indent=4, ensure_ascii=False)


# -----------------------------推荐图片---------------------------------------------------------------
# 将用户输入关键词翻译成英文，使得Unsplash推荐的图片更准确
def translate(content):
    # 初始化 DeepSeek 客户端
    key = Config.DEEPSEEK_API_KEY
    client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "你是一个中英文翻译助手，只需将用户输入的中文翻译为准确的英文搜索词，用于英文搜索引擎使用，不要解释，也不要加引号。"
            },
            {
                "role": "user",
                "content": f"请将以下内容翻译为英文：{content}"
            }
        ],
        stream=False
    )

    translated = response.choices[0].message.content.strip()
    return translated


# 根据关键词推荐图片资源（使用 Unsplash API）
def recommend_images(keyword):
    access_key = Config.UNSPLASH_ACCESS_KEY
    translated_keyword = translate(keyword)  # 👈 替换为 DeepSeek 翻译

    api_url = f'https://api.unsplash.com/photos/random?query={translated_keyword}&count=4&client_id={access_key}'

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return f"❌ 无法获取图片资源：{e}"

    try:
        image_data = response.json()
        image_urls = [img['urls']['regular'] for img in image_data]
    except Exception as e:
        return f"⚠️ 图片解析失败：{e}"

    if not image_urls:
        return "🔍 没有找到相关的图片资源。"

    return image_urls


# 返回JSON格式的图片资源
def recommend_pictures(keyword):
    # print("正在推荐图片资源，请稍候...\n")

    result = {
        "images": []
    }

    # 获取图片
    image_urls = recommend_images(keyword)
    if isinstance(image_urls, list):
        result["images"] = image_urls
    else:
        result["images"] = [image_urls]  # 错误信息也放进去（可选）

    # 输出为 JSON 字符串
    json_result = json.dumps(result, indent=4, ensure_ascii=False)
    return json_result

    # 可选：保存为文件
    # with open("media_results.json", "w", encoding="utf-8") as f:
    #     f.write(json_result)
    #     print("\n✅ 已保存为 media_results.json")


# ✅ 示例调用
if __name__ == "__main__":
    keyword = "牛顿第一定律"
    result = generate_final_markdown(keyword)
    print(result)
    pictures_json = recommend_pictures(keyword)
    print(pictures_json)

