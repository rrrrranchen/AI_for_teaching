from app.utils.database import db
from datetime import datetime
from app.models.relationship import teacher_class, student_class, course_courseclass

class Courseclass(db.Model):
    __tablename__ = 'courseclass'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    invite_code = db.Column(db.String(20), unique=True)  # 添加邀请码字段

    teachers = db.relationship('User', secondary=teacher_class, back_populates='teacher_courseclasses', lazy='joined')
    students = db.relationship('User', secondary=student_class, back_populates='student_courseclasses', lazy='joined')
    courses = db.relationship('Course', secondary=course_courseclass, back_populates='courseclasses', lazy='joined')

    def __repr__(self):
        return f'<Courseclass {self.name}>'