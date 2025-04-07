# app/models/user.py
from app.utils.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.models.relationship import teacher_class, student_class

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('student', 'teacher'), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    signature = db.Column(db.String(200), nullable=True)
    avatar = db.Column(db.String(256), nullable=True)  # 添加头像字段，存储头像的 URL 或本地路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 定义与 Courseclass 的多对多关系
    teacher_courseclasses = db.relationship('Courseclass', secondary=teacher_class, back_populates='teachers', lazy='joined')
    student_courseclasses = db.relationship('Courseclass', secondary=student_class, back_populates='students', lazy='joined')

    # 添加 posts 属性，表示用户发布的帖子
    posts = db.relationship('ForumPost', back_populates='author')

    # 添加 comments 属性，表示用户发布的评论
    comments = db.relationship('ForumComment', back_populates='author')

    # 添加 liked_posts 属性，表示用户点赞的帖子
    liked_posts = db.relationship('ForumPostLike', back_populates='user')

    # 添加 favorites 属性，表示用户收藏的帖子
    favorites = db.relationship('ForumFavorite', back_populates='user')

    # 添加 teaching_design_versions 属性，表示用户创建的教学设计版本
    teaching_design_versions = db.relationship('TeachingDesignVersion', back_populates='author')

    # 添加 teaching_designs 属性，表示用户创建的教学设计
    teaching_designs = db.relationship('TeachingDesign', back_populates='creator')
    analysis_reports = db.relationship('StudentAnalysisReport', back_populates='student')
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'