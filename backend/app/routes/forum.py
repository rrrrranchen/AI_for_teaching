import random
import string
from flask import Blueprint, render_template, request, jsonify, session
from pymysql import IntegrityError
from sqlalchemy import func, select
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.courseclass import Courseclass
from app.models.course import Course
from app.models.user import User
from app.models.relationship import teacher_class,student_class,course_courseclass
from app.models.forumpost_tag import ForumPost
from app.models.teachingdesignversion import TeachingDesignVersion

forum_bp=Blueprint('forum',__name__)

@forum_bp.route('/posts', methods=['POST'])
def create_post():
    data = request.json
    title = data.get('title')
    content = data.get('content')
    author_id = data.get('author_id')
    teaching_design_version_ids = data.get('teaching_design_version_ids', [])  # 获取教学设计版本 ID 数组

    if not title or not content or not author_id:
        return jsonify({'error': 'Missing required fields'}), 400

    # 创建帖子
    new_post = ForumPost(title=title, content=content, author_id=author_id)
    db.session.add(new_post)
    db.session.commit()

    # 如果有传入教学设计版本 ID 数组，则将帖子与这些版本关联
    if teaching_design_version_ids:
        for version_id in teaching_design_version_ids:
            teaching_design_version = TeachingDesignVersion.query.get(version_id)
            if teaching_design_version:
                new_post.teaching_design_versions.append(teaching_design_version)
            else:
                return jsonify({'error': f'Teaching Design Version with ID {version_id} not found'}), 404

        db.session.commit()

    return jsonify({'message': 'Post created successfully', 'post_id': new_post.id}), 201

