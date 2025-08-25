from datetime import datetime
import os
import json
from pathlib import Path
from typing import List, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
from langchain_text_splitters import TokenTextSplitter
from tqdm import tqdm

# --------------------------------------------------
# 1. 读环境变量
# --------------------------------------------------
load_dotenv()

# --------------------------------------------------
# 2. 初始化 DeepSeek
# --------------------------------------------------
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_base="https://api.deepseek.com/v1",
    openai_api_key="sk-ca9d2a314fda4f8983f61e292a858d17",
    temperature=0.5,
)

# --------------------------------------------------
# 3. 构造提示词模板（要求返回 JSON）
# --------------------------------------------------
system_prompt = (
    "你是知识图谱专家，请根据提供的 Markdown 文本，按以下规则与 JSON Schema 输出图谱：\n"
    "输出约束：\n"
    "1. 仅返回合法 JSON，禁止解释。\n"
    "2. nodes id 与 name 保持一致。\n"
    "3. nodes总数少于36 个。\n"
    "4. 相同类目节点在数组中连续排列。\n"
    "5. 用中文描述，专业英文术语保留英文。\n"
    "6. 颜色用十六进制，鲜明区分主题。\n"
    "7. 最终categories的数量必须小于5"
    "8. 节点的category必须出现在categories出现的category"
    "{{\n"
    "  \"nodes\": [\n"
    "    {{\n"
    "      \"id\": str,\n"
    "      \"name\": str,\n"
    "      \"symbolSize\": int,            // 30-80\n"
    "      \"category\": str\n"
    "    }}\n"
    "  ],\n"
    "  \"links\": [\n"
    "    {{\n"
    "      \"source\": str,\n"
    "      \"target\": str,\n"
    "      \"label\": str\n"
    "    }}\n"
    "  ],\n"
    "  \"categories\": [{{\"name\": str, \"itemStyle\": {{\"color\": str}}}}]\n"
    "}}\n"

)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", system_prompt+"{text}")
])
# --------------------------------------------------
# 4. 组装链
# --------------------------------------------------
chain = prompt | llm | JsonOutputParser()

# --------------------------------------------------
# 5. 工具函数：递归读取所有 .md 文件
# --------------------------------------------------
def read_all_md(folder_roots: list[str], max_tokens: int = 64_000) -> str:
    """
    读取所有 .md 后，整体截断到 max_tokens（默认 64k）。
    注意：会丢失尾部内容，但不会再触发 400。
    """
    all_text = []
    for root in folder_roots:
        for path in Path(root).rglob("*.md"):
            try:
                all_text.append(path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"⚠️  读取失败 {path}: {e}")

    full_text = "\n\n".join(all_text)

    # 如果总 token 数超过 max_tokens，就截断
    splitter = TokenTextSplitter(
        chunk_size=max_tokens,
        chunk_overlap=0,
        model_name="gpt-3.5-turbo"
    )
    chunks = splitter.split_text(full_text)
    return chunks[0]  # 只保留第一段

# --------------------------------------------------
# 6. 主函数：生成知识图谱
# --------------------------------------------------
def build_knowledge_graph(folder_roots: List[str],
                          save_dir: Optional[str] = None) -> Dict:
    """
    读取文件夹列表中的所有 .md，生成知识图谱。
    :param folder_roots: 要遍历的文件夹路径列表
    :param save_dir:     保存 JSON 的目录；None 则不保存
    :return:             知识图谱 dict（如果 save_dir 有值，会在 kg 中多一个键 _file_abs）
    """
    text = read_all_md(folder_roots)
    if not text.strip():
        raise ValueError("没有找到任何 md 文件或文件为空！")
    print(f"✅ 已读取所有 Markdown，共 {len(text)} 字符，正在请求 DeepSeek…")

    kg = chain.invoke({"text": text})

    if save_dir:
        save_path = Path(save_dir).expanduser().resolve()
        save_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = save_path / f"knowledge_graph_{timestamp}.json"

        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(kg, f, ensure_ascii=False, indent=2)

        file_abs = str(file_name.absolute())
        kg["_file_abs"] = file_abs          # 在返回字典里带上绝对路径
        print(f"🎉 知识图谱已保存至：{file_abs}")

    return kg


if __name__ == "__main__":
    # 支持传入多个文件夹
    folders = [
        "D:/AI_for_teaching/backend/app/static/knowledge/category/user_2_category_34"
    ]
    graph = build_knowledge_graph(folders,"D:/AI_for_teaching/backend/app/static/knowledge/graph")
    print(graph["_file_abs"])