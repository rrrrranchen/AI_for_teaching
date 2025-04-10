import os
import random
import string
import uuid
from venv import logger
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
from app.models.forumattachment import ForumAttachment
from app.models.forumcomment import ForumComment
from app.models.forumfavorite import ForumFavorite
from app.models.forumpostlike import ForumPostLike
from werkzeug.utils import secure_filename

forum_bp=Blueprint('forum',__name__)
# 检查用户是否登录
def is_logged_in():
    return 'user_id' in session
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

#创建帖子
@forum_bp.route('/posts', methods=['POST'])
def create_post():
    try:
        data = request.json
        title = data.get('title')
        content = data.get('content')
        author_id = data.get('author_id')
        teaching_design_version_ids = data.get('teaching_design_version_ids', [])

        if not title or not content or not author_id:
            return jsonify({'error': '缺少必要字段'}), 400

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        if current_user.id != author_id and current_user.role != 'admin':
            return jsonify({'error': '无权创建该帖子'}), 403

        new_post = ForumPost(title=title, content=content, author_id=author_id)
        db.session.add(new_post)
        db.session.commit()

        if teaching_design_version_ids:
            for version_id in teaching_design_version_ids:
                teaching_design_version = TeachingDesignVersion.query.get(version_id)
                if teaching_design_version:
                    new_post.teaching_design_versions.append(teaching_design_version)
                else:
                    return jsonify({'error': f'Teaching Design Version with ID {version_id} not found'}), 404
            db.session.commit()

        return jsonify({'message': '帖子创建成功', 'post_id': new_post.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建帖子失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

#获取所有帖子
@forum_bp.route('/posts', methods=['GET'])
def get_all_posts():
    try:
        posts = ForumPost.query.all()
        return jsonify([{
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author_id': post.author_id,
            'created_at': post.created_at,
            'updated_at': post.updated_at,
            'view_count': post.view_count,
            'is_pinned': post.is_pinned,
            'like_count': post.like_count
        } for post in posts]), 200
    except Exception as e:
        logger.error(f"获取帖子列表失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

#获取单个帖子  
@forum_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        post.view_count += 1
        db.session.commit()

        return jsonify({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author_id': post.author_id,
            'created_at': post.created_at,
            'updated_at': post.updated_at,
            'view_count': post.view_count,
            'is_pinned': post.is_pinned,
            'like_count': post.like_count
        }), 200
    except Exception as e:
        logger.error(f"获取帖子失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

#删除单个帖子
@forum_bp.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        if current_user.id != post.author_id and current_user.role != 'admin':
            return jsonify({'error': '无权删除该帖子'}), 403

        db.session.delete(post)
        db.session.commit()
        return jsonify({'message': '帖子已删除'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除帖子失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

#修改单个帖子的基本信息   
@forum_bp.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        if current_user.id != post.author_id and current_user.role != 'admin':
            return jsonify({'error': '无权修改该帖子'}), 403

        data = request.json
        post.title = data.get('title', post.title)
        post.content = data.get('content', post.content)
        db.session.commit()
        return jsonify({'message': '帖子已更新'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新帖子失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    
#点赞单个帖子
@forum_bp.route('/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        existing_like = ForumPostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()
        if existing_like:
            return jsonify({'error': '用户已经点赞'}), 400

        new_like = ForumPostLike(user_id=current_user.id, post_id=post_id)
        db.session.add(new_like)
        db.session.commit()
        return jsonify({'message': '点赞成功'}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"点赞帖子失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

#取消点赞单个帖子   
@forum_bp.route('/posts/<int:post_id>/like', methods=['DELETE'])
def unlike_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        existing_like = ForumPostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()
        if not existing_like:
            return jsonify({'error': '用户未点赞'}), 400

        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({'message': '取消点赞成功'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"取消点赞失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

#收藏单个帖子    
@forum_bp.route('/posts/<int:post_id>/favorite', methods=['POST'])
def favorite_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        tags = request.json.get('tags', '')
        existing_favorite = ForumFavorite.query.filter_by(user_id=current_user.id, post_id=post_id).first()
        if existing_favorite:
            return jsonify({'error': '用户已经收藏'}), 400

        new_favorite = ForumFavorite(user_id=current_user.id, post_id=post_id, tags=tags)
        db.session.add(new_favorite)
        db.session.commit()
        return jsonify({'message': '收藏成功'}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"收藏帖子失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

#取消收藏单个帖子    
@forum_bp.route('/posts/<int:post_id>/favorite', methods=['DELETE'])
def unfavorite_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        existing_favorite = ForumFavorite.query.filter_by(user_id=current_user.id, post_id=post_id).first()
        if not existing_favorite:
            return jsonify({'error': '用户未收藏'}), 400

        db.session.delete(existing_favorite)
        db.session.commit()
        return jsonify({'message': '取消收藏成功'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"取消收藏失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

#获取单个帖子的评论
@forum_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        comments = ForumComment.query.filter_by(post_id=post_id).all()
        return jsonify([{
            'id': comment.id,
            'content': comment.content,
            'author_id': comment.author_id,
            'created_at': comment.created_at
        } for comment in comments]), 200
    except Exception as e:
        logger.error(f"获取评论失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    
#添加评论
@forum_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        data = request.json
        content = data.get('content')
        parent_id = data.get('parent_id')

        if not content:
            return jsonify({'error': '缺少必要字段'}), 400

        new_comment = ForumComment(
            content=content,
            author_id=current_user.id,
            post_id=post_id,
            parent_id=parent_id
        )
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({'message': '评论已添加', 'comment_id': new_comment.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加评论失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    

#删除单个评论
@forum_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    try:
        comment = ForumComment.query.get(comment_id)
        if not comment:
            return jsonify({'error': '评论不存在'}), 404

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        if current_user.id != comment.author_id and current_user.role != 'admin':
            return jsonify({'error': '无权删除该评论'}), 403

        db.session.delete(comment)
        db.session.commit()
        return jsonify({'message': '评论已删除'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除评论失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join('static', 'uploads','forumattachments')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#为单个帖子上传附件
@forum_bp.route('/posts/<int:post_id>/attachments', methods=['POST'])
def upload_attachment(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        if current_user.id != post.author_id and current_user.role != 'admin':
            return jsonify({'error': '无权上传附件'}), 403

        # 检查是否有文件在请求中
        if 'file' not in request.files:
            return jsonify({'error': '没有文件部分'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400

        if file and allowed_file(file.filename):
            # 生成唯一的文件名
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(project_root, UPLOAD_FOLDER, unique_filename)

            # 确保上传目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 保存文件
            file.save(file_path)

            # 保存附件信息到数据库
            new_attachment = ForumAttachment(
                post_id=post_id,
                file_path=os.path.join(UPLOAD_FOLDER, unique_filename),
                uploader_id=current_user.id,
                display_name=request.form.get('display_name', filename)
            )
            db.session.add(new_attachment)
            db.session.commit()

            return jsonify({'message': '附件已上传', 'attachment_id': new_attachment.id}), 201

        return jsonify({'error': '不允许的文件类型'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"上传附件失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
#获取单个帖子的附件
@forum_bp.route('/posts/<int:post_id>/attachments', methods=['GET'])
def get_attachments(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        attachments = ForumAttachment.query.filter_by(post_id=post_id).all()
        return jsonify([{
            'id': attachment.id,
            'file_path': attachment.file_path,
            'uploader_id': attachment.uploader_id,
            'display_name': attachment.display_name,
            'created_at': attachment.created_at
        } for attachment in attachments]), 200
    except Exception as e:
        logger.error(f"获取附件失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    
#删除单个帖子的附件
@forum_bp.route('/attachments/<int:attachment_id>', methods=['DELETE'])
def delete_attachment(attachment_id):
    try:
        attachment = ForumAttachment.query.get(attachment_id)
        if not attachment:
            return jsonify({'error': '附件不存在'}), 404

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        if current_user.id != attachment.uploader_id and current_user.role != 'admin':
            return jsonify({'error': '无权删除该附件'}), 403

        # 删除文件系统中的文件
        file_path = os.path.join(project_root, attachment.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)

        # 删除数据库中的记录
        db.session.delete(attachment)
        db.session.commit()
        return jsonify({'message': '附件已删除'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除附件失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    
#获取用户收藏的帖子
@forum_bp.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        if current_user.id != user_id and current_user.role != 'admin':
            return jsonify({'error': '无权查看该用户的收藏'}), 403

        favorites = ForumFavorite.query.filter_by(user_id=user_id).all()
        return jsonify([{
            'id': favorite.id,
            'post_id': favorite.post_id,
            'created_at': favorite.created_at,
            'tags': favorite.tags
        } for favorite in favorites]), 200
    except Exception as e:
        logger.error(f"获取用户收藏失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

#为单个帖子添加教学设计版本    
@forum_bp.route('/posts/<int:post_id>/design_versions', methods=['POST'])
def add_design_version_to_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        if current_user.id != post.author_id and current_user.role != 'admin':
            return jsonify({'error': '无权为该帖子添加教学设计版本'}), 403

        data = request.json
        version_id = data.get('version_id')

        if not version_id:
            return jsonify({'error': '缺少教学设计版本ID'}), 400

        version = TeachingDesignVersion.query.get(version_id)
        if not version:
            return jsonify({'error': '教学设计版本不存在'}), 404

        # 检查是否已经关联
        if version in post.teaching_design_versions:
            return jsonify({'error': '该帖子已经关联了该教学设计版本'}), 400

        post.teaching_design_versions.append(version)
        db.session.commit()
        return jsonify({'message': '教学设计版本已成功添加到帖子', 'version_id': version.id}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"为帖子添加教学设计版本失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

#获取单个帖子的所有教学设计版本    
@forum_bp.route('/posts/<int:post_id>/design_versions', methods=['GET'])
def get_design_versions_for_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        versions = post.teaching_design_versions
        versions_data = [{
            'version_id': version.id,
            'design_id': version.design_id,
            'version': version.version,
            'content': version.content,
            'author_id': version.author_id,
            'created_at': version.created_at.isoformat() if version.created_at else None,
            'updated_at': version.updated_at.isoformat() if version.updated_at else None,
            'level': version.level,
            'recommendation_score': version.recommendation_score
        } for version in versions]

        return jsonify({'data': versions_data}), 200
    except Exception as e:
        logger.error(f"获取帖子的教学设计版本失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    
#为单个帖子移除教学设计版本
@forum_bp.route('/posts/<int:post_id>/design_versions/<int:version_id>', methods=['DELETE'])
def remove_design_version_from_post(post_id, version_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        if current_user.id != post.author_id and current_user.role != 'admin':
            return jsonify({'error': '无权从该帖子移除教学设计版本'}), 403

        version = TeachingDesignVersion.query.get(version_id)
        if not version:
            return jsonify({'error': '教学设计版本不存在'}), 404

        if version not in post.teaching_design_versions:
            return jsonify({'error': '该帖子未关联该教学设计版本'}), 400

        post.teaching_design_versions.remove(version)
        db.session.commit()
        return jsonify({'message': '教学设计版本已成功从帖子中移除', 'version_id': version.id}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"从帖子移除教学设计版本失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500