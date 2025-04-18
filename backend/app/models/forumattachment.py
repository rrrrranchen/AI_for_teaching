from datetime import datetime
from bson import ObjectId
from app.utils.database import db

class ForumAttachment(db.Model):
    __tablename__ = 'forum_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'))
    file_path = db.Column(db.String(255), nullable=True)  # 新增路径字段
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    post = db.relationship('ForumPost', back_populates='attachments')
    uploader = db.relationship('User')
    
    