
from datetime import datetime

from bson import ObjectId
from app.utils.database import db


class ForumFavorite(db.Model):
    __tablename__ = 'forum_favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.Column(db.String(100))  # 收藏标签（可选）
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='uq_user_post_favorite'),
    )
    
    user = db.relationship('User', back_populates='favorites')
    post = db.relationship('ForumPost', back_populates='favorites')