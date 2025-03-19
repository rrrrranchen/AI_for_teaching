from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app.utils.database import db

# 帖子表
class ForumPost(db.Model):
    __tablename__ = 'forum_post'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ForumPost {self.title}>'
