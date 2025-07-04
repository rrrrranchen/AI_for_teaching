from datetime import datetime
from app.utils.database import db
from sqlalchemy import Enum

class CategoryFileImage(db.Model):
    __tablename__ = 'category_files_images'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_file_id = db.Column(db.Integer, db.ForeignKey('category_files.id'), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(500))  # 可选的图片描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # 与CategoryFile的关系
    category_file = db.relationship('CategoryFile', back_populates='category_files_images', lazy='joined')

    def __repr__(self):
        return f'<Image {self.original_filename} (Sequence: {self.sequence})>'