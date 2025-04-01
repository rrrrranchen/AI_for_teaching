from app.utils.database import db
from datetime import datetime

class TeachingDesign(db.Model):
    __tablename__ = 'teaching_design'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    current_version_id = db.Column(db.Integer)  # 当前生效版本ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # 关系定义
    course = db.relationship('Course', back_populates='teaching_designs')
    versions = db.relationship('TeachingDesignVersion', back_populates='design', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<TeachingDesign {self.title}>'

