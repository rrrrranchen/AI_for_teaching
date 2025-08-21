import os
from langchain_community.embeddings import DashScopeEmbedding

EMBED_MODEL = DashScopeEmbedding(
    model="text-embedding-v4",
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
)