from datetime import datetime
from app.utils.database import db


class ForumComment(db.Model):
    __tablename__ = 'forum_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('forum_comments.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    author = db.relationship('User', back_populates='comments')
    post = db.relationship('ForumPost', back_populates='comments')
    replies = db.relationship('ForumComment', backref=db.backref('parent', remote_side=[id]))



