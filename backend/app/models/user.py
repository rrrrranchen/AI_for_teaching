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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 定义与 Courseclass 的多对多关系
    courseclasses = db.relationship('Courseclass', secondary=teacher_class, back_populates='teachers', lazy='dynamic')
    student_courseclasses = db.relationship('Courseclass', secondary=student_class, back_populates='students', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'