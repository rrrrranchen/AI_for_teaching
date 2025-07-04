from datetime import datetime
from app.models.relationship import courseclass_knowledge_base
from sqlalchemy import Enum
from app.utils.database import db
from app.models.relationship import category_knowledge_base
class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_base'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    stored_basename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    is_system = db.Column(db.Boolean, default=False)
    need_update = db.Column(db.Boolean,default=False)
    base_type = db.Column(Enum('structural', 'non_structural'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('User', backref='knowledge_bases')

    courseclasses = db.relationship('Courseclass', secondary=courseclass_knowledge_base, back_populates='knowledge_bases', lazy='joined')
    categories = db.relationship('Category', secondary=category_knowledge_base, back_populates='knowledge_bases')

    def __repr__(self):
        return f'<KnowledgeBase {self.name}>'