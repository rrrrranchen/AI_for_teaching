from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.forumpost import ForumPost
from app.models.forumtag import ForumTag


forum_bp=Blueprint('forum',__name__)
def is_logged_in():
    return 'user_id' in session

# 创建帖子
@forum_bp.route('/post', methods=['POST'])
def create_post():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    title = data.get('title')
    content = data.get('content')
    author_id = session['user_id']  # 使用当前登录用户的 ID
    tag_ids = data.get('tag_ids', [])

    if not title or not content:
        return jsonify({"error": "Missing required fields"}), 400

    post = ForumPost(title=title, content=content, author_id=author_id)
    db.session.add(post)
    db.session.flush()  

    
    for tag_id in tag_ids:
        tag = ForumTag.query.get(tag_id)
        if tag:
            post.tags.append(tag)

    db.session.commit()
    return jsonify({"message": "Post created successfully", "post_id": post.id}), 201


