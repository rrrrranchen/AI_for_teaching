import requests

url='https://mineru.net/api/v4/extract/task'
header = {
    'Content-Type':'application/json',
    'Authorization':'Bearer eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI4NjMwMDg1MSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc1MTUyMzYyMiwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTUwNTAxMjU2NjAiLCJvcGVuSWQiOm51bGwsInV1aWQiOiIwYmIxYjRlMi0wMjc5LTQ4MzgtOGI2MC1iNDVhNmU3Y2Y4MWQiLCJlbWFpbCI6IiIsImV4cCI6MTc1MjczMzIyMn0.ebk7ZczL0BK64f7ZVtYr4gSf6IixaBAn801Oh7tP2xW61O9uwUOFAax7yxXlx5uPcb3dh8gncbhFOavaFWr5AQ'
}
data = {
    'url':'https://knowledge-file12.oss-cn-chengdu.aliyuncs.com/20250703/c63f3932-fee6-4cfb-913e-4eb39ba61e50_274f1d6f-2e9a-4a6c-a486-1eb7eeea112f_06.%E8%A1%8C%E4%B8%BA%E5%9E%8B%E6%A8%A1%E5%BC%8FPDF.pdf',
    'is_ocr':True,
    'enable_formula': False,
}

# res = requests.post(url,headers=header,json=data)
# print(res.json())
# print(res.json()["data"])


import requests
task_id='91e6e908-71ec-45a0-a626-2a1e3fa1050d'
url = f'https://mineru.net/api/v4/extract/task/{task_id}'
header = {
    'Content-Type':'application/json',
    'Authorization':'Bearer eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI4NjMwMDg1MSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc1MTUyMzYyMiwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTUwNTAxMjU2NjAiLCJvcGVuSWQiOm51bGwsInV1aWQiOiIwYmIxYjRlMi0wMjc5LTQ4MzgtOGI2MC1iNDVhNmU3Y2Y4MWQiLCJlbWFpbCI6IiIsImV4cCI6MTc1MjczMzIyMn0.ebk7ZczL0BK64f7ZVtYr4gSf6IixaBAn801Oh7tP2xW61O9uwUOFAax7yxXlx5uPcb3dh8gncbhFOavaFWr5AQ'
}

res = requests.get(url, headers=header)
print(res.status_code)
print(res.json())
print(res.json()["data"])