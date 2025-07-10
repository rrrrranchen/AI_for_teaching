from datetime import datetime
from app.utils.database import db
from app.models.user import User

class CourseClassApplication(db.Model):
    __tablename__ = 'courseclass_application'
    
    # 主键
    id = db.Column(db.Integer, primary_key=True)
    
    # 外键（明确指向users表）
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    courseclass_id = db.Column(db.Integer, db.ForeignKey('courseclass.id'), nullable=False)
    
    # 申请状态（示例字段）
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending/approved/rejected
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed_date = db.Column(db.DateTime)
    
    # 附加信息
    message = db.Column(db.Text)
    admin_notes = db.Column(db.Text)
    
    # 明确的关系配置（关键修改部分）
    student = db.relationship(
        'User',
        foreign_keys=[student_id],
        backref=db.backref('student_applications', lazy='dynamic')
    )
    
    teacher = db.relationship(
        'User',
        foreign_keys=[teacher_id],
        backref=db.backref('teacher_applications', lazy='dynamic')
    )
    
    courseclass = db.relationship(
        'Courseclass',
        back_populates='class_applications'  # 匹配Courseclass中的关系名称
    )
    
    # 辅助方法
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'teacher_id': self.teacher_id,
            'courseclass_id': self.courseclass_id,
            'status': self.status,
            'application_date': self.application_date.isoformat() if self.application_date else None,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'message': self.message
        }
    
    def __repr__(self):
        return f'<CourseClassApplication {self.id} - Student:{self.student_id} Course:{self.courseclass_id}>'