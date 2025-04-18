from datetime import datetime
from bson import ObjectId
from app.utils.database import db
from app.models.forumcomment import ForumComment
from app.models.forumattachment import ForumAttachment
from app.models.forumpostlike import ForumPostLike
from app.models.forumfavorite import ForumFavorite
forum_post_tags = db.Table('forum_post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('forum_posts.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('forum_tags.id'))
)
class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)
    favorite_count = db.Column(db.Integer, default=0)  
    like_count = db.Column(db.Integer, default=0)      
    
    # 关系定义
    author = db.relationship('User', back_populates='posts')
    comments = db.relationship('ForumComment', back_populates='post')
    attachments = db.relationship('ForumAttachment', back_populates='post')
    likes = db.relationship('ForumPostLike', back_populates='post')
    favorites = db.relationship('ForumFavorite', back_populates='post')
    tags = db.relationship('ForumTag', secondary=forum_post_tags, backref=db.backref('posts', lazy='dynamic'))

    def update_counts(self):
        """更新收藏人数和点赞人数"""
        self.like_count = len(self.likes)
        self.favorite_count = len(self.favorites)
    
class ForumTag(db.Model):
    __tablename__ = 'forum_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)