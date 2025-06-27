import os
from openai import OpenAI
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.dashscope import (
    DashScopeEmbedding,
    DashScopeTextEmbeddingModels,
    DashScopeTextEmbeddingType,
)
from llama_index.postprocessor.dashscope_rerank import DashScopeRerank
from create_kb import *

DB_PATH = "VectorStore"
TMP_NAME = "tmp_abcd"
EMBED_MODEL = DashScopeEmbedding(
    model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V2,
    text_type=DashScopeTextEmbeddingType.TEXT_TYPE_DOCUMENT,
)

# 设置嵌入模型
Settings.embed_model = EMBED_MODEL

def get_model_response(multi_modal_input, history, model, temperature, max_tokens, history_round, db_name, similarity_threshold, chunk_cnt, deepseek_api_key=None):
    prompt = history[-1][0]
    tmp_files = multi_modal_input['files']
    
    # 根据模型选择API端点
    if "deepseek" in model.lower():
        base_url = "https://api.deepseek.com"
        api_key = "sk-b7550aa67ed840ffacb5ca051733802c"  # 使用环境变量或默认key
    else:
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        api_key = "sk-48f34d4f9c6948cbaa5198ab455f1224"
    
    if os.path.exists(os.path.join("File", TMP_NAME)):
        db_name = TMP_NAME
    elif tmp_files:
        create_tmp_kb(tmp_files)
        db_name = TMP_NAME
    
    print(f"prompt:{prompt},tmp_files:{tmp_files},db_name:{db_name}")
    
    try:
        dashscope_rerank = DashScopeRerank(top_n=chunk_cnt, return_documents=True)
        storage_context = StorageContext.from_defaults(
            persist_dir=os.path.join(DB_PATH, db_name)
        )
        index = load_index_from_storage(storage_context)
        print("index获取完成")
        retriever_engine = index.as_retriever(
            similarity_top_k=20,
        )
        # 获取chunk
        retrieve_chunk = retriever_engine.retrieve(prompt)
        print(f"原始chunk为：{retrieve_chunk}")
        try:
            results = dashscope_rerank.postprocess_nodes(retrieve_chunk, query_str=prompt)
            print(f"rerank成功，重排后的chunk为：{results}")
        except:
            results = retrieve_chunk[:chunk_cnt]
            print(f"rerank失败，chunk为：{results}")
        chunk_text = ""
        chunk_show = ""
        for i in range(len(results)):
            if results[i].score >= similarity_threshold:
                chunk_text = chunk_text + f"## {i+1}:\n {results[i].text}\n"
                chunk_show = chunk_show + f"## {i+1}:\n {results[i].text}\nscore: {round(results[i].score,2)}\n"
        print(f"已获取chunk：{chunk_text}")
        prompt_template = f"请参考以下内容：{chunk_text}，以合适的语气回答用户的问题：{prompt}。如果参考内容中有图片链接也请直接返回。"
    except Exception as e:
        print(f"异常信息：{e}")
        prompt_template = prompt
        chunk_show = ""
    
    history[-1][-1] = ""
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )                
    system_message = {'role': 'system', 'content': 'You are a helpful assistant.'}
    messages = []
    history_round = min(len(history), history_round)
    for i in range(history_round):
        messages.append({'role': 'user', 'content': history[-history_round+i][0]})
        messages.append({'role': 'assistant', 'content': history[-history_round+i][1]})
    messages.append({'role': 'user', 'content': prompt_template})
    messages = [system_message] + messages
    
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True
    )
    
    assistant_response = ""
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            assistant_response += chunk.choices[0].delta.content
            history[-1][-1] = assistant_response
            yield history, chunk_show