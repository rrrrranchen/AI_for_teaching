from datetime import datetime
import os
from app.utils.database import db
import json  # 用于 JSON 序列化

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    courseclass_id = db.Column(db.Integer, db.ForeignKey('courseclass.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    json_path = db.Column(db.String(500), nullable=True)  # 存储 JSON 字符串
    name = db.Column(db.Text, nullable=False, default='新建会话')
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def set_content(self, messages):
        """
        把对话列表规范化后序列化写入 json_path 对应的文件；
        若 json_path 为空则自动生成唯一文件名。
        """
        # 1. 统一成 list
        if isinstance(messages, str):
            try:
                messages = json.loads(messages)
            except json.JSONDecodeError:
                messages = []

        if not isinstance(messages, list):
            messages = []

        # 2. 规范化字段
        normalized = []
        for idx, msg in enumerate(messages):
            if isinstance(msg, dict):
                normalized.append({
                    "id": msg.get("id", idx),
                    "role": str(msg.get("role", "")),
                    "content": str(msg.get("content", "")),
                    **{k: v for k, v in msg.items() if k not in {"id", "role", "content"}}
                })

        # 3. 准备文件路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        chat_dir = os.path.join(project_root, 'static', 'chat')
        os.makedirs(chat_dir, exist_ok=True)

        if not self.json_path:
            filename = f"chat_{self.id}_{int(datetime.utcnow().timestamp())}.json"
            self.json_path = os.path.join('static', 'chat', filename).replace('\\', '/')

        full_path = os.path.join(project_root, self.json_path)

        # 4. 写入磁盘
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(normalized, f, ensure_ascii=False, indent=2)
            # 5. 更新数据库字段
            db.session.add(self)
            db.session.commit()
        except (IOError, OSError) as e:
            db.session.rollback()
            raise RuntimeError(f"Failed to save chat history: {e}")

    def get_content(self):
        """获取对话记录，确保返回列表"""
        if not self.json_path:
            return []

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_json_path = os.path.join(project_root, self.json_path)

        # 文件不存在则返回空列表
        if not os.path.isfile(local_json_path):
            return []

        try:
            with open(local_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 如果文件解析后不是列表，返回空列表
                if not isinstance(data, list):
                    return []
                return data
        except (json.JSONDecodeError, IOError, OSError):
            # JSON 解析失败或文件读取失败时返回空列表
            return []