
from datetime import datetime
from app.utils.database import db

class StudentAnalysisReport(db.Model):
    __tablename__ = 'student_analysis_report'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    courseclass_id = db.Column(db.Integer, db.ForeignKey('courseclass.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    report_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联到学生
    student = db.relationship('User', foreign_keys=[student_id], back_populates='analysis_reports')
    
    # 关联到课程班或课程
    courseclass = db.relationship('Courseclass', foreign_keys=[courseclass_id], back_populates='student_reports')
    course = db.relationship('Course', foreign_keys=[course_id], back_populates='student_reports')

    def __repr__(self):
        return f'<StudentAnalysisReport {self.student_id} for Courseclass {self.courseclass_id} / Course {self.course_id}>'

