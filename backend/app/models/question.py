from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app.utils.database import db

# 题目表
class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    type = db.Column(db.Enum('choice', 'fill', 'short_answer'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.Integer)
    timing = db.Column(db.Enum('pre_class', 'post_class'), nullable=False)  

    def __repr__(self):
        return f'<Question {self.id}>'