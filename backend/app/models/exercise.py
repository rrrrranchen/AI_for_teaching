from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app.utils.database import db

class Exercise(db.Model):
    __tablename__ = 'exercise'

    id = db.Column(db.Integer, primary_key=True)
    lesson_plan_id = db.Column(db.Integer, db.ForeignKey('lesson_plan.id'), nullable=False)
    type = db.Column(db.Enum('choice', 'fill', 'short_answer', name='exercise_type'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    lesson_plan = db.relationship('LessonPlan', backref=db.backref('exercises', lazy=True))
    
    def __repr__(self):
        return f'<Exercise {self.id}>'