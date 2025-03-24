from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app.utils.database import db
# 学生答题记录表
class StudentAnswer(db.Model):
    __tablename__ = 'student_answer'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('courseclass.id'), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    time_spent = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<StudentAnswer {self.id}>'