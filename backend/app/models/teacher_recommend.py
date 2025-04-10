from app.utils.database import db
from datetime import datetime

class TeacherRecommend(db.Model):
    __tablename__ = 'teacher_recommend'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teaching_design_id = db.Column(db.Integer, db.ForeignKey('teaching_design.id'), nullable=False)
    video_recommendations = db.Column(db.Text, nullable=True)  # Markdown 格式文本
    image_recommendations = db.Column(db.JSON, nullable=True)  # JSON 格式存储图片 URL 列表
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 关系定义
    user = db.relationship('User', back_populates='teacher_recommendations')
    teaching_design = db.relationship('TeachingDesign', back_populates='teacher_recommendations')

    def __repr__(self):
        return f'<TeacherRecommend {self.id}>'