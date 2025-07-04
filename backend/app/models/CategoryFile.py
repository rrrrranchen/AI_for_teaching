from datetime import datetime
from app.utils.database import db

from sqlalchemy import Enum

class CategoryFile(db.Model):
    __tablename__ = 'category_files'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_file_path=db.Column(db.String(500), nullable=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(Enum('structural', 'non_structural'), nullable=False)  # 新增文件类型字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    category = db.relationship('Category', back_populates='category_files', lazy='joined')
    is_public = db.Column(db.Boolean, default=False)
    category_files_images = db.relationship('CategoryFileImage', back_populates='category_file', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<CategoryFile {self.name} ({self.file_type})>'