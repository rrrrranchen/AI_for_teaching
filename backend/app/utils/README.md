## 文件结构说明

### 核心功能模块
- `ai_chat.py`  
  知识库问答系统实现，提供基于知识库的智能问答功能

- `create_cat.py`  
  创建和管理资源类目的实现模块

- `create_kb.py`  
  知识库创建和管理功能实现

- `keywords_search.py`  
  关键词搜索功能实现，支持快速检索知识库内容

### 文件处理模块
- `file_upload.py`
  文件上传功能实现，包含完整的上传处理流程

- `file_validators.py`
  文件类型验证器，确保上传文件的安全性

- `fileparser.py`
  文件元数据解析器，提取上传文件的元信息

- `secure_filename.py`
  文件名安全校验模块，防止不安全文件名

### 辅助功能模块
- `database.py`
  数据库初始化脚本，包含数据模型定义和连接配置

- `plan2ppt.py`
  PPT自动生成功能，可根据模板生成演示文稿

- `preview_generator.py`
  预览图生成模块，为上传资源自动生成预览图像

### 推荐系统模块
- `recommend_to_students.py`
  学生个性化资源推荐算法实现

- `recommend_to_teachers.py`
  教师个性化资源推荐算法实现