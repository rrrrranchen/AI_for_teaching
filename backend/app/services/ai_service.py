from sparkai.llm.llm import ChatSparkLLM
from sparkai.core.messages import ChatMessage


SPARKAI_URL = 'wss://spark-api.xf-yun.com/v4.0/chat'

SPARKAI_APP_ID = 'fdc65b4b'
SPARKAI_API_SECRET = 'ZDFmMzg5Yjk2ZTVhMmNhNjM2Nzc2ZmMz'
SPARKAI_API_KEY = 'bd45dc727ac09175b09d3c2f5b2b993c'

SPARKAI_DOMAIN = '4.0Ultra'

def generate_lesson_plan(title, description):
    """
    调用AI服务生成教案内容
    :param title: 教案标题
    :param description: 教案描述
    :return: 生成的教案内容
    """
    # 初始化AI服务
    spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )

    # 构建请求消息
    prompt = f"根据以下标题和描述生成一个教案内容:\n标题: {title}\n描述: {description}"
    messages = [ChatMessage(role="user", content=prompt)]

    # 调用AI服务生成内容
    response = spark.generate([messages])

    # 提取生成的教案内容
    if response and len(response.generations) > 0:
        generated_content = response.generations[0][0].text
        return generated_content
    else:
        return "无法生成教案内容，请稍后重试。"
    
    
