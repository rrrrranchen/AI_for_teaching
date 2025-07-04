from datetime import datetime
from app.models.relationship import category_knowledge_base
from sqlalchemy import Enum
from app.utils.database import db
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    stored_categoryname = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    category_type = db.Column(Enum('structural', 'non_structural'), nullable=False)
    category_files = db.relationship('CategoryFile', back_populates='category', lazy='joined')
    is_public = db.Column(db.Boolean, default=False)
    is_system = db.Column(db.Boolean, default=False)
    knowledge_bases = db.relationship('KnowledgeBase', secondary=category_knowledge_base, back_populates='categories')

    def __repr__(self):
        return f'<Category {self.name}>'