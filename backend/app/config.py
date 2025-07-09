import os

class Config:
    DEEPSEEK_API_KEY="sk-ca9d2a314fda4f8983f61e292a858d17"
    DASHSCOPE_API_KEY="sk-48f34d4f9c6948cbaa5198ab455f1224"
    MINERU_API_TOKEN='eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI4NjMwMDg1MSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc1MTUyMzYyMiwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTUwNTAxMjU2NjAiLCJvcGVuSWQiOm51bGwsInV1aWQiOiIwYmIxYjRlMi0wMjc5LTQ4MzgtOGI2MC1iNDVhNmU3Y2Y4MWQiLCJlbWFpbCI6IiIsImV4cCI6MTc1MjczMzIyMn0.ebk7ZczL0BK64f7ZVtYr4gSf6IixaBAn801Oh7tP2xW61O9uwUOFAax7yxXlx5uPcb3dh8gncbhFOavaFWr5AQ'
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


