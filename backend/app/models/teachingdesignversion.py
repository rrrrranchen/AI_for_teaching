from app.utils.database import db
from datetime import datetime
from app.models.teaching_design import TeachingDesign



teaching_design_question = db.Table(
    'teaching_design_question',
    db.Column('version_id', db.Integer, db.ForeignKey('teaching_design_version.id'), primary_key=True),
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Index('idx_tdq_version_question', 'version_id', 'question_id')
)

teaching_design_post = db.Table(
    'teaching_design_post',
    db.Column('version_id', db.Integer, db.ForeignKey('teaching_design_version.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('forum_posts.id'), primary_key=True),
    db.Index('idx_tdp_version_post', 'version_id', 'post_id')
)
class TeachingDesignVersion(db.Model):
    __tablename__ = 'teaching_design_version'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    design_id = db.Column(db.Integer, db.ForeignKey('teaching_design.id'), nullable=False)
    version = db.Column(db.String(50), nullable=False, default='v1')
    content = db.Column(db.Text, nullable=False)  # 可存储JSON格式的详细教学设计
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.String(50), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    recommendation_score = db.Column(db.Float, default=0.0, comment="推荐指数(0-100分)")  
    
    # 关联关系
    design = db.relationship('TeachingDesign', back_populates='versions')
    author = db.relationship('User', back_populates='teaching_design_versions')
    
    
    
    questions = db.relationship(
        'Question',
        secondary=teaching_design_question,
        collection_class=set,
        backref=db.backref('teaching_design_versions', lazy='dynamic')
    )
    
    posts = db.relationship(
        'ForumPost',
        secondary=teaching_design_post,
        collection_class=set,
        backref=db.backref('teaching_design_versions', lazy='dynamic')
    )

    # 复合唯一约束
    __table_args__ = (
        db.UniqueConstraint('design_id', 'version', name='uix_design_version'),
    )

    def __repr__(self):
        return f'<Version {self.version} of Design {self.design_id}>'

