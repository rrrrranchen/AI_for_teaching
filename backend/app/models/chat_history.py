from datetime import datetime
from app.utils.database import db
import json  # 用于 JSON 序列化

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    courseclass_id = db.Column(db.Integer, db.ForeignKey('courseclass.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=True)  # 存储 JSON 字符串
    name = db.Column(db.Text, nullable=False, default='新建会话')
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def set_content(self, messages):
        """确保存储的是平铺的对话数组"""
        if isinstance(messages, str):
            try:
                # 如果传入的是字符串，尝试解析
                messages = json.loads(messages)
            except json.JSONDecodeError:
                messages = []
        
        # 确保是列表格式
        if not isinstance(messages, list):
            messages = []
        
        # 规范化消息格式
        normalized_messages = []
        for idx, msg in enumerate(messages):
            if isinstance(msg, dict):
                normalized_messages.append({
                    "id": msg.get("id", idx),
                    "role": msg.get("role", ""),
                    "content": msg.get("content", ""),
                    **{k: v for k, v in msg.items() if k not in ["id", "role", "content"]}
                })
        
        # 序列化存储
        self.content = json.dumps(normalized_messages, ensure_ascii=False)

    def get_content(self):
        """获取对话记录，确保返回列表"""
        if not self.content:
            return []
        
        try:
            content = json.loads(self.content)
            # 确保返回的是列表
            return content if isinstance(content, list) else []
        except json.JSONDecodeError:
            return []