from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app.utils.database import db
from app.models.relationship import post_tag
# 论坛标签表
class ForumTag(db.Model):
    __tablename__ = 'forum_tag'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label_name = db.Column(db.String(50), nullable=False)
    label_description = db.Column(db.Text)

    # 定义多对多关系
    posts = db.relationship('ForumPost', secondary=post_tag, back_populates='tags')

    def __repr__(self):
        return f'<ForumTag {self.label_name}>'