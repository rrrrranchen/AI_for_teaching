# app/models/user.py
from app.utils.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.models.relationship import teacher_class, student_class
from app.models.classanalysisreport import ClassAnalysisReport
from app.models.studentanalysisreport import StudentAnalysisReport
from app.models.student_recommend import StudentRecommend
from app.models.TeacherOperationLog import TeacherOperationLog
from app.models.StudentOperationLog import StudentOperationLog
from app.models.AdminOperationLog import AdminOperationLog
from app.models.KnowledgeBase import KnowledgeBase
from app.models.Category import Category
from app.models.CategoryFile import CategoryFile
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('student', 'teacher', 'admin'), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    signature = db.Column(db.String(200), nullable=True)
    avatar = db.Column(db.String(256), nullable=True)  # 添加头像字段，存储头像的 URL 或本地路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    teacher_courseclasses = db.relationship('Courseclass', secondary=teacher_class, back_populates='teachers', lazy='joined')
    student_courseclasses = db.relationship('Courseclass', secondary=student_class, back_populates='students', lazy='joined')
    posts = db.relationship('ForumPost', back_populates='author')
    comments = db.relationship('ForumComment', back_populates='author')
    liked_posts = db.relationship('ForumPostLike', back_populates='user')
    favorites = db.relationship('ForumFavorite', back_populates='user')
    teaching_design_versions = db.relationship('TeachingDesignVersion', back_populates='author')
    teacher_recommendations = db.relationship('TeacherRecommend', back_populates='user')
    student_recommendations = db.relationship('StudentRecommend', back_populates='user')
    operation_logs = db.relationship('TeacherOperationLog', back_populates='user')
    teaching_designs = db.relationship('TeachingDesign', back_populates='creator')
    analysis_reports = db.relationship('StudentAnalysisReport', back_populates='student')
    student_operation_logs = db.relationship('StudentOperationLog', back_populates='student')
    admin_operation_logs = db.relationship('AdminOperationLog', back_populates='admin')
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'