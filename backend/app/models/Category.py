from datetime import datetime
from app.utils.database import db
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    knowledge_base_id = db.Column(db.Integer, db.ForeignKey('knowledge_base.id'), nullable=False)
    knowledge_base = db.relationship('KnowledgeBase', back_populates='categories', lazy='joined')
    category_files = db.relationship('CategoryFile', back_populates='category', lazy='joined')

    def __repr__(self):
        return f'<Category {self.name}>'