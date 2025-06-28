from datetime import datetime
from app.utils.database import db

class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_base'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    categories = db.relationship('Category', back_populates='knowledge_base', lazy='joined')

    def __repr__(self):
        return f'<KnowledgeBase {self.name}>'