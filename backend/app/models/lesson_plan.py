from app.utils.database import db
from datetime import datetime
from app.models.user import User

class LessonPlan(db.Model):
    __tablename__ = 'lesson_plan'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 修改为 'users.id'
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    status = db.Column(db.Enum('draft', 'published', name='status'), default='draft')
    generated_by = db.Column(db.Enum('AI', 'manual', name='generated_by'), default='manual')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 外键关联
    teacher = db.relationship('User', backref=db.backref('lesson_plans', lazy=True))

    def __init__(self, teacher_id, title, description=None, content=None, status='draft', generated_by='manual'):
        self.teacher_id = teacher_id
        self.title = title
        self.description = description
        self.content = content
        self.status = status
        self.generated_by = generated_by

    def __repr__(self):
        return f'<LessonPlan {self.id} - {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'status': self.status,
            'generated_by': self.generated_by,
            'created_at': self.created_at.isoformat()
        }