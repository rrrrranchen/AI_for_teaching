# app/models/course.py
from app.utils.database import db
from datetime import datetime
from app.models.relationship import course_courseclass  # 导入关联表

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    
    courseclasses = db.relationship('Courseclass', secondary=course_courseclass, back_populates='courses')
    teaching_designs = db.relationship('TeachingDesign', back_populates='course')
    def __repr__(self):
        return f'<Course {self.name}>'