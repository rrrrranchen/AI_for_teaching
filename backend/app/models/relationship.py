from app.utils.database import db


teacher_class = db.Table(
    'teacher_class',
    db.Column('teacher_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('class_id', db.Integer, db.ForeignKey('courseclass.id'), primary_key=True)
)

student_class = db.Table(
    'student_class',
    db.Column('student_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('class_id', db.Integer, db.ForeignKey('courseclass.id'), primary_key=True)
)

# 课程-课程班关系表
course_courseclass = db.Table(
    'course_courseclass',
    db.Column('course_id', db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), primary_key=True),
    db.Column('courseclass_id', db.Integer, db.ForeignKey('courseclass.id', ondelete='CASCADE'), primary_key=True)
)

# 帖子-标签关联表
post_tag = db.Table(
    'post_tag',
    db.Column('post_id', db.Integer, db.ForeignKey('forum_post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('forum_tag.id'), primary_key=True)
)