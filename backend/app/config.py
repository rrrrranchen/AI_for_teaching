import os

class Config:
    DEEPSEEK_API_KEY="sk-ca9d2a314fda4f8983f61e292a858d17"
    DASHSCOPE_API_KEY="sk-48f34d4f9c6948cbaa5198ab455f1224"
    MINERU_API_TOKEN='eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI4NjMwMDg1MSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc1Mjc3MDIwMiwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTUwNTAxMjU2NjAiLCJvcGVuSWQiOm51bGwsInV1aWQiOiI3YmUzMTQ1YS0zOThhLTQxYWQtYTcwMi1kYTE2YTkxMGZjMTIiLCJlbWFpbCI6IiIsImV4cCI6MTc1Mzk3OTgwMn0.YvBYbkY1NzZK_YMywBeIjjxFGWBYxKN4yvc9nuZ3dY3HZ-wVWWjrnjAnEZtoJOFqnjfQzbdJ8qpbdygD9QMsUw'
    ALIYUN_ACCESS_KEY_ID=os.getenv('ALIYUN_ACCESS_KEY_ID')
    ALIYUN_ACCESS_KEY_SECRET=os.getenv('ALIYUN_ACCESS_KEY_SECRET')
    PUBLIC_DOMAIN='https://knowledge-file12.oss-cn-chengdu.aliyuncs.com'
    BUCKET_NAME='knowledge-file12'
    ENDPOINT='oss-cn-chengdu.aliyuncs.com'
    UNSPLASH_ACCESS_KEY='GimQwr2RGVg_h6Op_FSb11kctxHCWkom_-GWbQbwqOI'
    GRADER_PATH=r'C:\\Users\13925\\.cache\\huggingface\\hub\\paraphrase-multilingual-MiniLM-L12-v2'
    # 文件上传配置
    
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx', 'jpg', 'png', 'mp4', 'mp3','doc'}
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    
    # 预览图尺寸配置
    PREVIEW_SIZES = {
        'thumbnail': (200, 200),
        'medium': (800, 800),
        'large': (1200, 1200)
    }


