# 教备通: AI 辅助教学交互系统

## 系统要求
- 后端: Python 3.9+
- 数据库: MySQL

## 前端部署
请参考 `/frontend/README.md` 文件

## 后端部署

### 数据库配置
1. 新建一个空MySQL数据库
2. 修改 `backend/app/utils/database.py` 中的数据库连接配置
3. 运行后端服务后会自动生成所有数据表

### 依赖安装
```bash
pip install -r requirements.txt
```

## 后端配置与运行

### 语言模型配置
1. 安装并配置 `paraphrase-multilingual-MiniLM-L12-v2` 语言模型
2. 修改 `backend/app/config.py` 中的 `GRADER_PATH` 为本地模型下载路径

### 环境变量配置
需要配置以下环境变量：
- `ALIYUN_ACCESS_KEY_ID`
- `ALIYUN_ACCESS_KEY_SECRET`
- `DASHSCOPE_API_KEY`

配置完成后请**重启编辑器**

### 后端运行命令
```bash
python backend/run.py
```

## 数据库迁移指南

### 配置步骤
1. 修改 `alembic.ini` 文件中的 `sqlalchemy.url` 配置

### 迁移命令
```bash
# 生成迁移脚本
alembic revision --autogenerate -m "Initial migration"

# 应用迁移
alembic upgrade head
```

## 注意事项
1. 确保所有配置修改后保存文件
2. 环境变量配置完成后需要重启相关服务
3. 数据库迁移前请备份现有数据
```