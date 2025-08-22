import os
import re
import uuid
import math
from pathlib import PurePosixPath
from http import HTTPStatus
from urllib.parse import urlparse, unquote
import requests
from dashscope import ImageSynthesis
import jieba
import jieba.analyse

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
folder = os.path.join(project_root,'static','picture')

# ---------------- 公开调用入口 ----------------
def generate_teaching_images_from_content(content: str,
                                          output_dir=folder,
                                          words_per_group=3,
                                          images_per_group=1,
                                          ratio="1:1"):
    """
    根据教学设计 Markdown 字符串，按关键词分组多次生成图片。

    新增参数:
        ratio (str): 图片长宽比，可选 "1:1", "16:9", "9:16", "3:4", "4:3"
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. 提取关键词
    keywords = extract_keywords_from_md(content)
    if not keywords:
        print("未能提取到关键词")
        return []

    # 2. 关键词分组
    groups = group_keywords(keywords, words_per_group)
    print(f"[关键词分组] {groups}")

    # 3. 按组生成图片，并把 ratio 传下去
    all_paths = []
    for idx, g in enumerate(groups, 1):
        prompt = prompt_per_group(g, idx)
        paths = generate_images_with_dashscope(prompt,
                                               output_dir,
                                               images_per_group,
                                               prefix=f"g{idx}",
                                               ratio=ratio)   # 透传 ratio
        all_paths.extend(paths)

    return all_paths

# ---------------- 关键词相关 ----------------
def extract_keywords_from_md(md_content):
    """
    从 Markdown 内容中提取最多 10 个关键词
    """
    clean_text = clean_markdown(md_content)
    # 强制限制 10 个
    keywords = jieba.analyse.extract_tags(clean_text, topK=10, withWeight=False)
    return keywords

def clean_markdown(text):
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`.*?`', '', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'\*\*|\*|__|_', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def group_keywords(keywords, k):
    """将关键词列表按每 k 个一组拆分"""
    return [keywords[i:i+k] for i in range(0, len(keywords), k)]

def prompt_per_group(group_words, group_idx):
    """为每组关键词构造独立提示词"""
    prompt = (f"主题组 {group_idx}：{', '.join(group_words)}。"
              "用于教学辅助说明图片")
    return prompt

# ---------------- DashScope 调用 ----------------
def generate_images_with_dashscope(prompt, output_dir, n,
                                   prefix="", ratio="1:1"):
    """
    使用 DashScope 生成图片
    新增 ratio 参数，支持 "1:1", "16:9", "9:16", "3:4", "4:3"
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("未设置 DASHSCOPE_API_KEY")
        return []

    # 比例 → 像素 映射
    ratio_map = {
        "1:1":  "1024*1024",
        "16:9": "1280*720",
        "9:16": "720*1280",
        "3:4":  "768*1024",
        "4:3":  "1024*768"
    }
    size = ratio_map.get(ratio, "1024*1024")  # 默认正方形

    paths = []
    try:
        rsp = ImageSynthesis.call(
            api_key=api_key,
            model="wan2.2-t2i-flash",
            prompt=prompt,
            n=n,
            size=size
        )
        if rsp.status_code == HTTPStatus.OK:
            for i, res in enumerate(rsp.output.results):
                remote = PurePosixPath(unquote(urlparse(res.url).path)).parts[-1]
                local = f"{prefix}_{uuid.uuid4().hex}_{remote}" if prefix else f"{uuid.uuid4().hex}_{remote}"
                local_path = os.path.join(output_dir, local)
                rpath = os.path.join('static','picture',local)
                with open(local_path, 'wb') as f:
                    f.write(requests.get(res.url).content)
                paths.append(rpath)
                print(f"[保存] {local_path} (比例 {ratio})")
        else:
            print(f"[错误] {rsp.status_code} {rsp.code} {rsp.message}")
    except Exception as e:
        print(f"[异常] {e}")

    return paths

# ---------------- 示例 ----------------
if __name__ == "__main__":
    md = """
    # 《光合作用》教学设计
    教学目标：  
    - 理解光合作用的概念  
    - 掌握反应式及影响因素  
    - 培养实验探究能力  

    重点：光反应与暗反应  
    难点：能量转换过程
    """
    imgs = generate_teaching_images_from_content(md,
                                                 words_per_group=2,
                                                 images_per_group=1)
    print("最终生成图片：", imgs)