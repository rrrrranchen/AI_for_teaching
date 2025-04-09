import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import json

# 根据关键词推荐 Bilibili 视频链接
def recommend_bilibili_videos(keyword):
    search_url = f'https://search.bilibili.com/all?keyword={keyword}&from_source=nav_search&order=default'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return f"❌ 无法获取 Bilibili 视频资源：{e}"

    soup = BeautifulSoup(response.text, 'html.parser')

    # 更新选择器：根据 B站页面结构动态调整，下面是一个常见选择器（可根据调试结果适配）
    video_links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href')
        if href.startswith('//www.bilibili.com/video/') and href not in video_links:
            video_links.append('https:' + href)
        if len(video_links) >= 5:
            break

    if not video_links:
        return "🔍 没有找到相关的 Bilibili 视频资源。"

    return video_links


# 将用户输入关键词翻译成英文，使得Unsplash推荐的图片更准确
def translate(keyword):
    # 初始化 DeepSeek 客户端
    key = 'sk-b7550aa67ed840ffacb5ca051733802c'
    client = OpenAI(api_key=key, base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "你是一个中英文翻译助手，只需将用户输入的中文关键词翻译为准确的英文搜索词，用于英文搜索引擎使用，不要解释，也不要加引号。"
            },
            {
                "role": "user",
                "content": f"请将以下关键词翻译为英文：{keyword}"
            }
        ],
        stream=False
    )

    translated = response.choices[0].message.content.strip()
    return translated


# 根据关键词推荐图片资源（使用 Unsplash API）
def recommend_images(keyword):
    access_key = 'GimQwr2RGVg_h6Op_FSb11kctxHCWkom_-GWbQbwqOI'
    translated_keyword = translate(keyword)  # 👈 替换为 DeepSeek 翻译

    api_url = f'https://api.unsplash.com/photos/random?query={translated_keyword}&count=3&client_id={access_key}'

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


# 返回JSON格式的视频与图片资源
def recommend_media_resources(keyword):
    print("正在推荐视频和图片资源，请稍候...\n")

    result = {
        "keyword": keyword,
        "videos": [],
        "images": []
    }

    # 获取视频
    video_links = recommend_bilibili_videos(keyword)
    if isinstance(video_links, list):
        result["videos"] = video_links
    else:
        result["videos"] = [video_links]  # 错误信息也放进去（可选）

    # 获取图片
    image_urls = recommend_images(keyword)
    if isinstance(image_urls, list):
        result["images"] = image_urls
    else:
        result["images"] = [image_urls]  # 错误信息也放进去（可选）

    # 输出为 JSON 字符串
    json_result = json.dumps(result, indent=4, ensure_ascii=False)
    print(json_result)

    # 可选：保存为文件
    with open("media_results.json", "w", encoding="utf-8") as f:
        f.write(json_result)
        print("\n✅ 已保存为 media_results.json")


# 运行程序
if __name__ == "__main__":
    keyword = input("请输入要查找的多媒体资源的关键词：")
    recommend_media_resources(keyword)