from datetime import datetime
from app.utils.database import db

# 学生答题记录表
class StudentAnswer(db.Model):
    __tablename__ = 'student_answer'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('courseclass.id'), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    correct_percentage = db.Column(db.Integer, nullable=False)  
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    modified_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<StudentAnswer {self.id}>'