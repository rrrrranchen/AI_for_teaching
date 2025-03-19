from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app.utils.database import db
# 论坛标签表
class ForumTag(db.Model):
    __tablename__ = 'forum_tag'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    label_name = db.Column(db.String(50), nullable=False)
    label_description = db.Column(db.Text)

    def __repr__(self):
        return f'<ForumTag {self.label_name}>'