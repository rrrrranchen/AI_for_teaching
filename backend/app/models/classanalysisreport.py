from datetime import datetime
from app.utils.database import db
class ClassAnalysisReport(db.Model):
    __tablename__ = 'class_analysis_report'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    courseclass_id = db.Column(db.Integer, db.ForeignKey('courseclass.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    report_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联到课程班或课程
    courseclass = db.relationship('Courseclass', foreign_keys=[courseclass_id], back_populates='class_reports')
    course = db.relationship('Course', foreign_keys=[course_id], back_populates='class_reports')

    def __repr__(self):
        return f'<ClassAnalysisReport for Courseclass {self.courseclass_id} / Course {self.course_id}>'