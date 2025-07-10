from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import json

# 设置 API Key
key = 'sk-b7550aa67ed840ffacb5ca051733802c'
client = OpenAI(api_key=key, base_url="https://api.deepseek.com")


# 提取关键词的函数
def extract_keywords_from_report(report):
    # 使用 DeepSeek 进行关键词提取
    prompt = f"""
请从以下报告中提取出 错题相关的一个具体知识点，要求：
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


# 步骤4：主调用函数，组装最终 JSON 格式输出
def generate_final_json(keyword):
    # 获取推荐视频链接
    links = recommend_bilibili_videos(keyword)
    if isinstance(links, str):
        return links  # 如果获取失败，返回错误信息

    # 获取每个视频的标题和简介
    video_infos = [fetch_video_info(link) for link in links]

    # 对视频标题和简介进行润色
    ai_result = polish_title_description(video_infos)

    # 拆分 AI 输出，逐条绑定原始链接
    result_blocks = ai_result.strip().split("\n\n")

    # 组装成 JSON 格式数据
    result_list = []

    for i, block in enumerate(result_blocks):
        if i >= len(video_infos):
            break
        video_info = video_infos[i]
        # 将视频信息组织成字典
        result_dict = {
            "资源推荐": block.strip().split("\n")[0],  # 资源标题是块的第一行
            "资源简介": block.strip().split("\n")[1],  # 资源简介是块的第二行
            "相关链接": video_info["link"]  # 相关链接是原始视频链接
        }
        result_list.append(result_dict)

    # 转换为 JSON 格式的字符串并返回
    json_result = json.dumps(result_list, ensure_ascii=False, indent=4)
    return json_result


# 示例调用
if __name__ == "__main__":
    # 示例报告
    report = """# 学情分析报告 - 操作系统第一章
    ## 一、总体表现统计
    - **答题总数**: 11题
    - **正确答题数**: 8题
    - **错误答题数**: 3题
    - **总体正确率**: 72.7%
    - **错误率**: 27.3%

    ## 二、错题分布与典型错误分析
    ### 1. 错题分布
    | 题号 | 题目内容 | 学生答案 | 正确答案 | 错误类型 |
    |------|----------|----------|----------|----------|
    | 85   | 以下哪个设备用于连接不同网络段？ | A. 集线器 | C. 路由器 | 概念混淆 |
    | 90   | 以下哪个协议用于网页浏览？ | A. HTTP | A. HTTP | 无错误(系统可能标记错误) |
    | 93   | 以下哪个协议用于安全的网页浏览？ | B. HTTPS | B. HTTPS | 无错误(系统可能标记错误) |

    ### 2. 典型错误分析
    1. **网络设备概念混淆**：
       - 在题目85中，学生错误选择了"集线器"作为连接不同网络段的设备
       - 正确设备应为"路由器"，这表明学生对网络设备功能区分不够清晰
       - 集线器工作在物理层，而路由器工作在网络层，用于连接不同网络

    2. **系统标记问题**：
       - 题目90和93显示学生答案与正确答案一致但被标记为错误
       - 可能是系统记录错误或数据输入问题
       - 需要进一步核实这两题的评分情况

    ## 三、知识掌握情况
    ### 1. 掌握良好的领域
    - 网络协议识别(ICMP、FTP、SMTP、Telnet、SNMP、POP3、DNS)
    - 网络安全设备识别(防火墙)
    - 基础网络服务协议对应关系

    ### 2. 需要加强的领域
    - 网络设备功能区分(路由器、交换机、集线器等)
    - 网络协议安全版本识别(HTTPS)
    - 网络层级概念理解

    ## 四、学习建议
    1. **网络设备专题复习**：
       - 制作网络设备对比表格，明确各设备工作层级和主要功能
       - 重点区分集线器、交换机、路由器和网关的异同
    2. **协议安全版本学习**：
       - 理解HTTP与HTTPS的关系和区别
       - 学习SSL/TLS加密原理
    3. **实践建议**：
       - 使用网络模拟软件(如Packet Tracer)搭建简单网络拓扑
       - 观察不同网络设备的数据处理方式
    4. **错题整理**：
       - 建立错题本，重点记录网络设备相关概念
       - 对系统标记有疑问的题目进行核实
    5. **延伸学习**：
       - 学习OSI七层模型，理解各层协议和设备
       - 了解现代网络架构中的SDN技术
    """

    # 提取关键词
    keywords = extract_keywords_from_report(report)
    print(keywords)
    # 根据关键词生成推荐视频
    result = generate_final_json(keywords)
    print(result)
