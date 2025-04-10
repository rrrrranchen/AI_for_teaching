# app/models/student_recommend.py
from app.utils.database import db
from datetime import datetime

class StudentRecommend(db.Model):
    __tablename__ = 'student_recommend'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    type = db.Column(db.Enum('pre_class', 'post_class'), nullable=False)  # 类型分为课前和课后
    content = db.Column(db.Text, nullable=False)  # 存储 markdown 格式的文本内容
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 定义与 User 和 Course 的关系
    user = db.relationship('User', back_populates='student_recommendations')
    course = db.relationship('Course', back_populates='student_recommendations')

    def __repr__(self):
        return f'<StudentRecommend {self.id}>'