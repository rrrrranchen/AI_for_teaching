from datetime import datetime
import os
import random
import string
import uuid
from venv import logger
from flask import Blueprint, json, render_template, request, jsonify, session
from pymysql import IntegrityError
from sqlalchemy import Integer, cast, func, select
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.courseclass import Courseclass
from app.models.course import Course
from app.models.user import User
from app.models.relationship import teacher_class,student_class,course_courseclass
from app.models.forumpost_tag import ForumPost, ForumTag,forum_post_tags
from app.models.teachingdesignversion import TeachingDesignVersion
from app.models.forumattachment import ForumAttachment
from app.models.forumcomment import ForumComment
from app.models.forumfavorite import ForumFavorite
from app.models.forumpostlike import ForumPostLike
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from app.models.teachingdesignversion import TeachingDesignVersion
from app.models.teaching_design import TeachingDesign
forum_bp=Blueprint('forum',__name__)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join('static', 'uploads','forumattachments')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# 检查用户是否登录
def is_logged_in():
    return 'user_id' in session
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None
from sqlalchemy import or_

def search_posts(keyword):
    # 搜索帖子标题、内容和标签
    posts = ForumPost.query.join(ForumPost.tags).filter(
        or_(
            ForumPost.title.ilike(f'%{keyword}%'),
            ForumPost.content.ilike(f'%{keyword}%'),
            ForumTag.name.ilike(f'%{keyword}%')
        )
    ).order_by(
        # 按优先级排序：标题 > 标签 > 内容
        ForumPost.title.ilike(f'%{keyword}%').desc(),
        ForumTag.name.ilike(f'%{keyword}%').desc(),
        ForumPost.content.ilike(f'%{keyword}%').desc()
    ).all()
    return posts
#上传附件路由
@forum_bp.route('/attachments', methods=['POST'])
def upload_attachment():
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        # 获取文件列表
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': '未上传文件'}), 400

        # 初始化返回结果
        results = []

        # 遍历文件列表
        for file in files:
            # 检查文件类型
            if not allowed_file(file.filename):
                return jsonify({'error': '不允许的文件类型'}), 400

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
                file_path=os.path.join(UPLOAD_FOLDER, unique_filename),
                uploader_id=current_user.id
            )
            db.session.add(new_attachment)
            db.session.commit()

            # 添加到返回结果
            results.append({
                'attachment_id': new_attachment.id,
                'file_path': new_attachment.file_path
            })

        return jsonify({
            'message': '附件上传成功',
            'results': results
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"上传附件失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    

# 创建帖子
@forum_bp.route('/posts', methods=['POST'])
def create_post():
    try:
        # 获取基本数据
        data = request.json
        title = data.get('title')
        content = data.get('content')
        author_id = get_current_user().id
        
        # 获取标签列表
        tags = data.get('tags', [])
        
        # 获取教学设计版本列表
        teaching_design_version_ids = data.get('teaching_design_version_ids', [])
        
        # 获取附件ID列表
        attachment_ids = data.get('attachment_ids', [])

        if not title or not content or not author_id:
            return jsonify({'error': '缺少必要字段'}), 400

        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        # 创建新帖子
        new_post = ForumPost(title=title, content=content, author_id=author_id)
        db.session.add(new_post)
        db.session.commit()

        # 处理标签
        new_tags = []
        for tag_name in tags:
            tag = ForumTag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = ForumTag(name=tag_name)
                db.session.add(tag)
                db.session.commit()
            new_post.tags.append(tag)
        
        # 处理教学设计版本
        if teaching_design_version_ids:
            for version_id in teaching_design_version_ids:
                version = TeachingDesignVersion.query.get(version_id)
                if not version:
                    return jsonify({'error': f'Teaching Design Version with ID {version_id} not found'}), 404
                if version.author_id != current_user.id:
                    return jsonify({'error': f'无权添加 Teaching Design Version with ID {version_id}，您不是该版本的作者'}), 403
                new_post.teaching_design_versions.append(version)
            db.session.commit()

        # 处理附件
        if attachment_ids:
            for attachment_id in attachment_ids:
                attachment = ForumAttachment.query.get(attachment_id)
                if not attachment:
                    return jsonify({'error': f'Attachment with ID {attachment_id} not found'}), 404
                if attachment.uploader_id != current_user.id:
                    return jsonify({'error': f'无权添加 Attachment with ID {attachment_id}，您不是该附件的上传者'}), 403
                attachment.post_id = new_post.id  # 更新附件的 post_id
                new_post.attachments.append(attachment)
            db.session.commit()

        return jsonify({
            'message': '帖子创建成功',
            'post_id': new_post.id,
            'tag_ids': [t.id for t in new_post.tags],
            'version_ids': [v.id for v in new_post.teaching_design_versions],
            'attachment_ids': [a.id for a in new_post.attachments]
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建帖子失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    


import logging

logger = logging.getLogger(__name__)



@forum_bp.route('/posts', methods=['GET'])
def get_all_posts():
    try:
        # 获取排序参数
        sort_by = request.args.get('sort_by', 'composite')  # 默认按综合排序
        if sort_by not in ['like_count', 'favorite_count', 'view_count', 'composite', 'created_at']:
            return jsonify({'error': '无效的排序参数'}), 400

        # 获取帖子列表，并预加载附件、作者信息和标签
        posts = ForumPost.query.options(
            joinedload(ForumPost.attachments),
            joinedload(ForumPost.author),
            joinedload(ForumPost.tags)
        ).all()

        # 定义权重系数
        alpha = 1.0  # 点赞数权重
        beta = 1.0   # 收藏数权重
        gamma = 0.5  # 浏览次数权重
        delta = 0.1  # 时间因子权重

        # 计算综合得分
        def calculate_score(post):
            # 计算时间因子，较新的帖子时间因子更高
            time_factor = (datetime.utcnow() - post.created_at).total_seconds() / (60 * 60 * 24)
            return (alpha * post.like_count +
                    beta * post.favorite_count +
                    gamma * post.view_count +
                    delta * time_factor)

        # 根据排序参数排序
        if sort_by == 'composite':
            posts.sort(key=calculate_score, reverse=True)
        elif sort_by == 'created_at':
            posts.sort(key=lambda post: post.created_at, reverse=True)
        else:
            posts.sort(key=lambda post: getattr(post, sort_by), reverse=True)

        current_user_id = session.get('user_id')

        # 构建返回数据
        post_data = []
        for post in posts:
            # 查找第一个图片附件
            first_image_attachment = None
            for attachment in post.attachments:
                if attachment.file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    first_image_attachment = attachment.file_path
                    break

            # 查询当前用户是否点赞了该帖子
            is_liked = False
            if current_user_id:
                like = ForumPostLike.query.filter_by(user_id=current_user_id, post_id=post.id).first()
                if like:
                    is_liked = True

            # 查询当前用户是否收藏了该帖子
            is_favorited = False
            if current_user_id:
                favorite = ForumFavorite.query.filter_by(user_id=current_user_id, post_id=post.id).first()
                if favorite:
                    is_favorited = True

            post_data.append({
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'author_id': post.author_id,
                'author_name': post.author.username,
                'author_avatar': post.author.avatar,
                'created_at': post.created_at,
                'updated_at': post.updated_at,
                'view_count': post.view_count,
                'like_count': post.like_count,
                'favorite_count': post.favorite_count,
                'is_liked': is_liked,
                'is_favorited': is_favorited,
                'first_image': first_image_attachment,
                'tags': [tag.name for tag in post.tags]
            })
            
        return jsonify(post_data), 200
    except Exception as e:
        logger.error(f"获取帖子列表失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    

@forum_bp.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        current_user = get_current_user()
        if current_user and current_user.id == post.author_id:
            # 如果当前用户是帖子的创建者，不增加浏览量
            pass
        else:
            # 如果当前用户不是帖子的创建者，增加浏览量
            post.view_count += 1
            db.session.commit()

        # 获取与帖子相关联的教学设计版本ID
        teaching_design_versions = [version.id for version in post.teaching_design_versions]

        # 获取与帖子相关联的附件ID
        attachments = [attachment.id for attachment in post.attachments]

        # 查询当前用户是否点赞了该帖子
        is_liked = False
        if current_user:
            like = ForumPostLike.query.filter_by(user_id=current_user.id, post_id=post.id).first()
            if like:
                is_liked = True

        # 查询当前用户是否收藏了该帖子
        is_favorited = False
        if current_user:
            favorite = ForumFavorite.query.filter_by(user_id=current_user.id, post_id=post.id).first()
            if favorite:
                is_favorited = True

        return jsonify({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author_id': post.author_id,
            'author_name': post.author.username,  
            'author_avatar': post.author.avatar,  
            'created_at': post.created_at,
            'updated_at': post.updated_at,
            'view_count': post.view_count,
            'like_count': post.like_count,
            'favorite_count': post.favorite_count,
            'teaching_design_versions': teaching_design_versions,
            'attachments': attachments,
            'is_liked': is_liked,
            'is_favorited': is_favorited
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

        # 获取帖子的所有附件
        attachments = ForumAttachment.query.filter_by(post_id=post_id).all()

        # 删除文件系统中的附件文件
        for attachment in attachments:
            file_path = os.path.join(project_root, attachment.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)

        # 删除数据库中的附件记录
        for attachment in attachments:
            db.session.delete(attachment)

        # 删除帖子与标签的关联记录
        db.session.execute(forum_post_tags.delete().where(forum_post_tags.c.post_id == post_id))

        # 删除帖子的评论
        comments = ForumComment.query.filter_by(post_id=post_id).all()
        for comment in comments:
            db.session.delete(comment)

        # 删除帖子的点赞记录
        likes = ForumPostLike.query.filter_by(post_id=post_id).all()
        for like in likes:
            db.session.delete(like)

        # 删除帖子的收藏记录
        favorites = ForumFavorite.query.filter_by(post_id=post_id).all()
        for favorite in favorites:
            db.session.delete(favorite)

        # 删除帖子记录
        db.session.delete(post)

        # 提交所有删除操作
        db.session.commit()

        return jsonify({'message': '帖子及所有相关数据已删除'}), 200
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

        # 获取 JSON 数据
        data = request.json

        # 更新帖子基本信息
        post.title = data.get('title', post.title)
        post.content = data.get('content', post.content)

        # 更新相关联的教学设计版本信息
        teaching_design_version_ids = data.get('teaching_design_version_ids', [])
        if teaching_design_version_ids:
            # 清除现有关联
            post.teaching_design_versions = []  # 使用赋值来清空关系
            # 添加新的关联
            for version_id in teaching_design_version_ids:
                version = TeachingDesignVersion.query.get(version_id)
                if not version:
                    return jsonify({'error': f'Teaching Design Version with ID {version_id} not found'}), 404
                if version.author_id != current_user.id:
                    return jsonify({'error': f'无权添加 Teaching Design Version with ID {version_id}，您不是该版本的作者'}), 403
                post.teaching_design_versions.append(version)

        # 更新相关联的附件信息
        attachment_ids = data.get('attachment_ids', [])
        if attachment_ids:
            # 找出需要删除的附件
            current_attachment_ids = {attachment.id for attachment in post.attachments}
            new_attachment_ids = set(attachment_ids)
            attachments_to_delete = current_attachment_ids - new_attachment_ids

            # 删除不再属于帖子的附件及其本地存储文件
            for attachment_id in attachments_to_delete:
                attachment = ForumAttachment.query.get(attachment_id)
                if attachment:
                    # 删除本地存储文件
                    file_path = os.path.join(project_root, attachment.file_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    # 删除数据库记录
                    db.session.delete(attachment)

            # 清除现有关联
            post.attachments = []  # 使用赋值来清空关系
            # 添加新的关联
            for attachment_id in attachment_ids:
                attachment = ForumAttachment.query.get(attachment_id)
                if not attachment:
                    return jsonify({'error': f'Attachment with ID {attachment_id} not found'}), 404
                if attachment.uploader_id != current_user.id:
                    return jsonify({'error': f'无权添加 Attachment with ID {attachment_id}，您不是该附件的上传者'}), 403
                post.attachments.append(attachment)

        db.session.commit()
        return jsonify({'message': '帖子及关联信息已更新'}), 200
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

        # 更新帖子的点赞人数
        post.update_counts()
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

        # 更新帖子的点赞人数
        post.update_counts()
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



        existing_favorite = ForumFavorite.query.filter_by(user_id=current_user.id, post_id=post_id).first()
        if existing_favorite:
            return jsonify({'error': '用户已经收藏'}), 400

        new_favorite = ForumFavorite(user_id=current_user.id, post_id=post_id)
        db.session.add(new_favorite)
        db.session.commit()

        # 更新帖子的收藏人数
        post.update_counts()
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

        # 更新帖子的收藏人数
        post.update_counts()
        db.session.commit()

        return jsonify({'message': '取消收藏成功'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"取消收藏失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

# 获取单个帖子的评论
@forum_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    try:
        post = ForumPost.query.get(post_id)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        # 查询所有评论
        comments = ForumComment.query.filter_by(post_id=post_id).all()

        # 获取所有评论作者的ID
        author_ids = {comment.author_id for comment in comments}

        # 一次性查询所有相关用户信息
        users = User.query.filter(User.id.in_(author_ids)).all()
        user_map = {user.id: user for user in users}

        # 构建评论数据
        comment_data = []
        for comment in comments:
            user = user_map.get(comment.author_id)
            if user:
                comment_info = {
                    'id': comment.id,
                    'content': comment.content,
                    'author_id': comment.author_id,
                    'author_name': user.username,
                    'author_avatar': user.avatar,
                    'created_at': comment.created_at,
                    'parent_id': comment.parent_id,
                    'replies': []  # 初始化回复列表
                }
                comment_data.append(comment_info)

        # 构建评论树结构
        comment_tree = []
        comment_map = {comment['id']: comment for comment in comment_data}

        for comment in comment_data:
            if comment['parent_id'] is None:
                comment_tree.append(comment)
            else:
                parent_comment = comment_map.get(comment['parent_id'])
                if parent_comment:
                    parent_comment['replies'].append(comment)

        return jsonify(comment_tree), 200

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

        # 递归删除所有子评论
        def delete_comment_and_replies(comment):
            for reply in comment.replies:
                delete_comment_and_replies(reply)
            db.session.delete(comment)

        delete_comment_and_replies(comment)
        db.session.commit()
        return jsonify({'message': '评论及所有回复已删除'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除评论失败: {str(e)}")
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
            'uploader_name':User.query.get(attachment.uploader_id).username,
            'created_at': attachment.created_at
        } for attachment in attachments]), 200
    except Exception as e:
        logger.error(f"获取附件失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    
    

# 获取用户收藏的帖子
@forum_bp.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        user_id = current_user.id
        # 使用 joinedload 加载帖子信息、附件、标签和作者信息
        favorites = ForumFavorite.query.options(
            joinedload(ForumFavorite.post).joinedload(ForumPost.attachments),
            joinedload(ForumFavorite.post).joinedload(ForumPost.tags),
            joinedload(ForumFavorite.post).joinedload(ForumPost.author)
        ).filter_by(user_id=user_id).all()

        # 构建返回数据
        favorite_data = []
        for favorite in favorites:
            post = favorite.post
            # 查找第一个图片附件
            first_image_attachment = None
            for attachment in post.attachments:
                if attachment.file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    first_image_attachment = attachment.file_path
                    break

            favorite_data.append({
                'id': favorite.id,
                'post_id': post.id,
                'post_title': post.title,
                'content': post.content,
                'author_id': post.author_id,
                'author_name': post.author.username,
                'author_avatar': post.author.avatar,
                'created_at': favorite.created_at,
                'tags': [tag.name for tag in post.tags],
                'first_image': first_image_attachment
            })

        return jsonify(favorite_data), 200
    except Exception as e:
        logger.error(f"获取用户收藏失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    
# 查询帖子
@forum_bp.route('/posts/search', methods=['GET'])
def search_posts_route():
    try:
        keyword = request.args.get('keyword')
        if not keyword:
            return jsonify({'error': '缺少搜索关键词'}), 400

         # 使用参数化查询防止SQL注入
        search_pattern = f"%{keyword}%"
        
        post_scores = db.session.query(
            ForumPost.id.label('post_id'),
            (func.sum(
                cast(ForumPost.title.ilike(search_pattern), Integer) * 3 +
                cast(ForumTag.name.ilike(search_pattern), Integer) * 2 +
                cast(ForumPost.content.ilike(search_pattern), Integer)
            ).label('match_score'))
        ).outerjoin(
            ForumPost.tags
        ).filter(
            or_(
                ForumPost.title.ilike(search_pattern),
                ForumPost.content.ilike(search_pattern),
                ForumTag.name.ilike(search_pattern)
            )
        ).group_by(ForumPost.id).subquery()

        # 2. 主查询
        posts_with_scores = db.session.query(
            ForumPost,
            post_scores.c.match_score
        ).outerjoin(
            post_scores, ForumPost.id == post_scores.c.post_id
        ).options(
            joinedload(ForumPost.attachments),
            joinedload(ForumPost.author),
            joinedload(ForumPost.tags)
        ).order_by(
            post_scores.c.match_score.desc(),
            ForumPost.created_at.desc()
        ).all()

        # 3. 构建响应数据
        post_data = []
        for post, score in posts_with_scores:
            # 获取作者信息（添加空值保护）
            author_name = post.author.username if post.author else None

            # 查找第一个图片附件
            first_image_attachment = next(
                (att.file_path for att in post.attachments 
                 if att.file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))),
                None
            )

            post_data.append({
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'author_id': post.author_id,
                'author_avatar': post.author.avatar,
                'created_at': post.created_at,
                'author_name': post.author.username,
                'view_count': post.view_count,
                'like_count': post.like_count,
                'favorite_count': post.favorite_count,
                'tags': [tag.name for tag in post.tags],
                'first_image': first_image_attachment 
            })

        return jsonify(post_data), 200
    except Exception as e:
        logger.error(f"搜索帖子失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    
# 获取当前登录用户的所有帖子
@forum_bp.route('/users/posts', methods=['GET'])
def get_user_posts():


    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': '请先登录'}), 401

        user_id = current_user.id
        # 预加载附件和标签
        posts = ForumPost.query.options(
            joinedload(ForumPost.attachments),
            joinedload(ForumPost.tags)
        ).filter_by(author_id=user_id).all()

        post_data = []
        for post in posts:
            # 查找第一个图片附件
            first_image_attachment = None
            for attachment in post.attachments:
                if attachment.file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    first_image_attachment = attachment.file_path
                    break

            post_data.append({
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'author_name': current_user.username,
                'author_avatar': current_user.avatar,
                'created_at': post.created_at,
                'updated_at': post.updated_at,
                'view_count': post.view_count,
                'like_count': post.like_count,
                'favorite_count': post.favorite_count,
                'tags': [tag.name for tag in post.tags],
                'first_image': first_image_attachment  # 添加第一个图片附件路径
            })

        return jsonify(post_data), 200
    except Exception as e:
        logger.error(f"获取用户帖子失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    

@forum_bp.route('/get_alltags', methods=['GET'])
def get_alltags():
    # 查询数据库获取所有标签
    tags = ForumTag.query.all()
    
    # 将标签对象列表转换为字典列表
    tag_list = [{'id': tag.id, 'name': tag.name} for tag in tags]
    
    # 返回 JSON 格式的数据
    return jsonify(tag_list)

@forum_bp.route('/recommended_designs', methods=['GET'])
def get_recommended_designs():
    try:
        # 获取推荐的公开教学设计（按推荐时间倒序，限制数量）
        recommended_designs = TeachingDesign.query.filter(
            TeachingDesign.is_public == True,
            TeachingDesign.is_recommended == True
        ).order_by(
            TeachingDesign.recommend_time.desc()
        ).limit(5).all()  # 限制获取5个

        # 构建返回数据
        designs_data = []
        for design in recommended_designs:
            # 获取当前版本
            current_version = TeachingDesignVersion.query.get(design.current_version_id)
            version_content = json.loads(current_version.content) if current_version and current_version.content else {}
            
            # 获取作者信息
            author = User.query.get(design.creator_id)
            
            designs_data.append({
                'id': design.id,
                'title': design.title,
                'course_id': design.course_id,
                'author_id': design.creator_id,
                'author_name': author.username if author else "未知用户",
                'author_avatar': author.avatar if author else None,
                'version_content': version_content.get('plan_content', '')[:200] + '...',  # 截取部分内容
                'recommend_time': design.recommend_time.isoformat() if design.recommend_time else None
            })

        return jsonify(designs_data), 200
    except Exception as e:
        logger.error(f"获取推荐教学设计失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500