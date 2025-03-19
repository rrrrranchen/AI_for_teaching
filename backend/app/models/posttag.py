from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app.utils.database import db
# 论坛标签-帖子关系表
class PostTag(db.Model):
    __tablename__ = 'post_tag'
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('forum_tag.id'), primary_key=True)

    def __repr__(self):
        return f'<PostTag post_id={self.post_id}, tag_id={self.tag_id}>'
