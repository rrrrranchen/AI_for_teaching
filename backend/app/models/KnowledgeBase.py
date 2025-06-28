from datetime import datetime
from app.utils.database import db

class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_base'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)  # 存储知识库相关文件的路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    categories = db.relationship('Category', back_populates='knowledge_base', lazy='joined')
    is_public = db.Column(db.Boolean, default=False)
    courseclasses = db.relationship('Courseclass', back_populates='knowledge_base', lazy='joined')  # 添加反向关系

    def __repr__(self):
        return f'<KnowledgeBase {self.name}>'