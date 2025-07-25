from app.utils.database import db
from datetime import datetime
from app.models.relationship import teacher_class, student_class, course_courseclass
from app.models.classanalysisreport import ClassAnalysisReport
from app.models.studentanalysisreport import StudentAnalysisReport
from app.models.relationship import courseclass_knowledge_base
class Courseclass(db.Model):
    __tablename__ = 'courseclass'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    invite_code = db.Column(db.String(20), unique=True)  # 添加邀请码字段
    image_path = db.Column(db.String(500), nullable=True)  # 新增图片存储路径字段
    is_public = db.Column(db.Boolean, default=False)
    knowledge_bases = db.relationship('KnowledgeBase', secondary=courseclass_knowledge_base, back_populates='courseclasses', lazy='joined')
    teachers = db.relationship('User', secondary=teacher_class, back_populates='teacher_courseclasses', lazy='joined')
    students = db.relationship('User', secondary=student_class, back_populates='student_courseclasses', lazy='joined')
    courses = db.relationship('Course', secondary=course_courseclass, back_populates='courseclasses', lazy='joined')
    # 添加级联删除设置
    student_reports = db.relationship(
        'StudentAnalysisReport', 
        back_populates='courseclass',
        cascade='all, delete-orphan'
    )
    
    class_reports = db.relationship(
        'ClassAnalysisReport', 
        back_populates='courseclass',
        cascade='all, delete-orphan'
    )
    
    class_applications = db.relationship(  # 使用新名称避免冲突
        'CourseClassApplication', 
        back_populates='courseclass',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Courseclass {self.name}>'
