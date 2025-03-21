from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.forumpost import ForumPost
from app.models.forumtag import ForumTag
from app.models.comment import Comment

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


# 更新帖子信息
@forum_bp.route('/post/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    post = ForumPost.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    
    if post.author_id != session['user_id']:
        return jsonify({"error": "Forbidden"}), 403

    data = request.json
    post.title = data.get('title', post.title)
    post.content = data.get('content', post.content)
    tag_ids = data.get('tag_ids', [])

    # 更新标签关系
    post.tags.clear()
    for tag_id in tag_ids:
        tag = ForumTag.query.get(tag_id)
        if tag:
            post.tags.append(tag)

    db.session.commit()
    return jsonify({"message": "Post updated successfully"})


# 获取所有帖子，所有人都可以获取帖子
@forum_bp.route('/posts', methods=['GET'])
def get_posts():
    posts = ForumPost.query.all()
    result = []
    for post in posts:
        post_data = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "author_id": post.author_id,
            "created_at": post.created_at.isoformat(),
            "tags": [{"id": tag.id, "label_name": tag.label_name} for tag in post.tags]
        }
        result.append(post_data)
    return jsonify(result)


# 获取单个帖子
@forum_bp.route('/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = ForumPost.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    post_data = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author_id": post.author_id,
        "created_at": post.created_at.isoformat(),
        "tags": [{"id": tag.id, "label_name": tag.label_name} for tag in post.tags]
    }
    return jsonify(post_data)




#删除帖子
@forum_bp.route('/post/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    post = ForumPost.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    # 检查是否是帖子的作者
    if post.author_id != session['user_id']:
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted successfully"})



# 创建评论
@forum_bp.route('/post/<int:post_id>/comment', methods=['POST'])
def create_comment(post_id):
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    content = data.get('content')
    parent_comment_id = data.get('parent_comment_id')

    if not content:
        return jsonify({"error": "Missing required fields"}), 400

    comment = Comment(
        post_id=post_id,
        author_id=session['user_id'],
        content=content,
        parent_comment_id=parent_comment_id
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify({"message": "Comment created successfully", "comment_id": comment.id}), 201


# 获取单个帖子的所有评论
@forum_bp.route('/post/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).all()
    result = []
    for comment in comments:
        comment_data = {
            "id": comment.id,
            "post_id": comment.post_id,
            "author_id": comment.author_id,
            "content": comment.content,
            "parent_comment_id": comment.parent_comment_id,
            "created_at": comment.created_at.isoformat()
        }
        result.append(comment_data)
    return jsonify(result)


#获取单个评论
@forum_bp.route('/comment/<int:comment_id>', methods=['GET'])
def get_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": "Comment not found"}), 404

    comment_data = {
        "id": comment.id,
        "post_id": comment.post_id,
        "author_id": comment.author_id,
        "content": comment.content,
        "parent_comment_id": comment.parent_comment_id,
        "created_at": comment.created_at.isoformat()
    }
    return jsonify(comment_data)

#删除某个评论
@forum_bp.route('/comment/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401

    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": "Comment not found"}), 404

    # 检查是否是评论的作者
    if comment.author_id != session['user_id']:
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(comment)
    db.session.commit()
    return jsonify({"message": "Comment deleted successfully"})


# 获取所有标签
@forum_bp.route('/tags', methods=['GET'])
def get_tags():
    tags = ForumTag.query.all()
    result = []
    for tag in tags:
        tag_data = {
            "id": tag.id,
            "label_name": tag.label_name,
            "label_description": tag.label_description
        }
        result.append(tag_data)
    return jsonify(result)

@forum_bp.route('/forum')
def forum_page():
    return render_template('forum.html')