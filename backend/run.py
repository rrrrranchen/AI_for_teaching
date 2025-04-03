from flask import current_app, jsonify
from app import create_app
from flask_cors import CORS

app = create_app()

# 启用 CORS 支持
CORS(app, origins=["http://localhost:8080"], supports_credentials=True)

@app.route("/")
def index():
    return "Hello, Flask Backend!"

if __name__ == "__main__":
    # 设置主机和端口
    host = "0.0.0.0"  # 允许外部访问
    port = 5000       # 后端运行端口
    
    # 启动 Flask 应用
    app.run(host=host, port=port, debug=True)
    