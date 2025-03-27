from app import create_app
from flask import send_from_directory
from flask_cors import CORS
import os

app = create_app()

# 启用 CORS 支持（根据前端地址调整）
CORS(app, resources={
    r"/api/*": {"origins": "*"},  # API接口跨域
    r"/static/*": {"origins": "*"}  # 静态资源跨域
}, supports_credentials=True)

# 添加静态资源路由
@app.route('/static/<path:filename>')
def serve_static(filename):
    root_dir = os.path.dirname(os.getcwd())
    static_dir = os.path.join(root_dir, 'backend', 'static')
    return send_from_directory(static_dir, filename)

@app.route("/")
def index():
    return "Hello, Flask Backend!"

if __name__ == "__main__":
    # 设置主机和端口
    host = "0.0.0.0"  # 允许外部访问
    port = 5000       # 后端运行端口

    # 启动 Flask 应用
    app.run(host=host, port=port, debug=True)