## 后端部署

### 数据库配置
1. 新建一个空MySQL数据库
2. 修改 `backend/app/utils/database.py` 中的数据库连接配置
3. 运行后端服务后会自动生成所有数据表

### 依赖安装
```bash
pip install -r requirements.txt
```

## 后端配置与运行指南

### 语言模型配置
1. 安装并配置 `paraphrase-multilingual-MiniLM-L12-v2` 语言模型
2. 修改 `backend/app/config.py` 中的 `GRADER_PATH` 为本地模型下载路径

### 环境变量配置
需要配置以下环境变量：
- `ALIYUN_ACCESS_KEY_ID`
- `ALIYUN_ACCESS_KEY_SECRET`
- `DASHSCOPE_API_KEY`

配置完成后请**重启编辑器**

### 后端运行
```bash
python backend/run.py
```

## 数据库迁移指南

使用 Alembic 进行数据库迁移操作：

### 配置步骤
1. 修改 `alembic.ini` 文件中的 `sqlalchemy.url` 配置

### 迁移命令
```bash
# 生成迁移脚本
alembic revision --autogenerate -m "Initial migration"

# 应用迁移
alembic upgrade head