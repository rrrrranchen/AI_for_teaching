from datetime import datetime
import os
import threading
import uuid
from venv import logger
from bson import ObjectId
from flask import Blueprint, app, current_app, redirect, render_template, request, jsonify, send_file, session
from jwt import InvalidKeyError
from sqlalchemy import func, select
from app.utils.database import db
from app.models.user import User
from app.models.courseclass import Courseclass
from app.models.resources import Metadata, MultimediaResource
from app.models.relationship import teacher_class
from app.utils.file_validators import allowed_file
from app.utils.fileparser import FileParser
from werkzeug.utils import secure_filename
from app.utils.preview_generator import generate_preview
from werkzeug.utils import safe_join  
from mongoengine.errors import DoesNotExist, ValidationError

from app.services.plan2ppt import generate_PPT
from app.models.ppttemplate import PPTTemplate
from app.models.teachingdesignversion import TeachingDesignVersion
resource_bp=Blueprint('resource',__name__)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join('static', 'uploads','techingresources')

# 检查用户是否登录
def is_logged_in():
    return 'user_id' in session
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None
# 检查当前用户是否为课程班的创建老师
def is_teacher_of_courseclass(courseclass_id):
    current_user = get_current_user()
    if not current_user or current_user.role != 'teacher':
        return False
    
    # 查询 teacher_class 表，检查当前用户是否为课程班的老师
    association = db.session.scalar(
        select(func.count()).where(
            teacher_class.c.teacher_id == current_user.id,
            teacher_class.c.class_id == courseclass_id
        )
    )
    return association > 0

def async_generate_ppt(app, course_id, teachingdesignversion_id, ppttemplate_id, title, username, user_id):
    with app.app_context():
        try:
            # 查询教学设计版本
            teaching_design_version = TeachingDesignVersion.query.filter_by(
                id=teachingdesignversion_id
            ).first()
            
            if not teaching_design_version:
                current_app.logger.error(f"Teaching design version not found: {teachingdesignversion_id}")
                return

            # 获取教学设计内容
            teaching_plan = teaching_design_version.content

            # 查询 PPT 模板
            ppt_template = PPTTemplate.query.filter_by(id=ppttemplate_id).first()
            if not ppt_template:
                current_app.logger.error(f"PPT template not found: {ppttemplate_id}")
                return

            # 获取模板路径
            template_path = ppt_template.url

            # 生成 PPT
            storage_path = generate_PPT(teaching_plan, template_path, username)
            
            current_app.logger.info(f"PPT 生成成功，临时存储路径: {storage_path}")

            # 生成唯一的文件名
            unique_filename = str(uuid.uuid4()) + ".pptx"
            final_storage_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            final_storage_path1 = os.path.join(project_root, final_storage_path)

            # 将 PPT 文件移动到最终存储路径
            os.rename(storage_path, final_storage_path1)
            current_app.logger.info(f"PPT 文件移动成功，最终存储路径: {final_storage_path1}")

            # 生成元数据
            parsed_meta = FileParser.parse_file(final_storage_path1)
            if 'error' in parsed_meta:
                os.remove(final_storage_path1)
                current_app.logger.error(f"元数据解析失败: {parsed_meta['error']}")
                return

            # 确保只包含 Metadata 模型中定义的字段
            valid_meta_fields = {
                'file_size', 'format', 'mime_type',
                'duration', 'resolution', 'bitrate',
                'page_count', 'word_count', 'author',
                'color_mode', 'dpi', 'extra'
            }
            cleaned_meta = {k: v for k, v in parsed_meta.items() if k in valid_meta_fields}

            # 生成预览图
            try:
                previews = generate_preview(final_storage_path1, unique_filename)
            except Exception as e:
                current_app.logger.error(f"预览图生成失败: {str(e)}")
                previews = {"thumbnail": "static/default_preview.jpg"}

            # 创建资源文档
            resource = MultimediaResource(
                type="presentation",  # PPT 类型
                title=title,  # 使用前端提供的标题
                description="自动生成的教学设计 PPT",
                course_id=course_id,
                designversion_id=teachingdesignversion_id,
                uploader_id=user_id,  # 使用传递的 user_id
                storage_path=final_storage_path,
                preview_urls=previews,
                metadata=Metadata(**{
                    'file_size': os.path.getsize(final_storage_path1),
                    'mime_type': "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    **cleaned_meta
                }),
                is_teaching_design=True  # 标记为教学设计 PPT
            )
            resource.save()
            current_app.logger.info(f"资源成功保存到 MongoDB，资源 ID: {resource.id}")
        except Exception as e:
            current_app.logger.error(f"生成 PPT 时出错: {str(e)}")

@resource_bp.route('/createPPT/<int:course_id>/<int:teachingdesignversion_id>/<int:ppttemplate_id>', methods=['POST'])
def generatePPT(course_id, teachingdesignversion_id, ppttemplate_id):
    # 从请求中获取标题
    title = request.args.get('title', default="教学设计 PPT", type=str)  # 从 URL 查询参数获取
    current_user = get_current_user()
    if not current_user:
        return jsonify({'message': '用户未登录'}), 401

    username = current_user.username
    user_id = current_user.id

    # 启动异步任务
    thread = threading.Thread(target=async_generate_ppt, args=(current_app._get_current_object(), course_id, teachingdesignversion_id, ppttemplate_id, title, username, user_id))
    thread.start()

    return jsonify({'message': 'PPT generation started'}), 202


@resource_bp.route('/resources', methods=['POST'])
def upload_resource():
    # 获取上传的文件
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file provided"}), 400

    # 检查文件类型是否允许
    is_allowed, validator = allowed_file(file.filename)
    if not is_allowed:
        return jsonify({"error": "File type not allowed"}), 400

    # 确保上传目录存在
    upload_folder = os.path.join(project_root, UPLOAD_FOLDER)
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # 获取安全的文件名
    secure_name = secure_filename(file.filename)

    # 检查文件名是否包含 .
    if '.' not in secure_name:
        return jsonify({"error": "File name does not contain an extension"}), 400

    # 分离文件名和扩展名
    name, ext = os.path.splitext(secure_name)

    # 生成唯一的文件名
    unique_filename = str(uuid.uuid4()) + ext

    # 保存文件
    relative_storage_path = os.path.join(UPLOAD_FOLDER, unique_filename)  # 相对路径
    absolute_storage_path = os.path.join(project_root, relative_storage_path)  # 绝对路径
    file.save(absolute_storage_path)
    
    # 验证文件内容
    if not validator(absolute_storage_path):
        os.remove(absolute_storage_path)
        return jsonify({"error": "File content does not match extension"}), 400

    # 解析表单数据
    form_data = {
        'title': request.form.get('title', name),
        'description': request.form.get('description', ''),
        'course_id': int(request.form.get('course_id', 0)),  # 提供默认值
        'designversion_id': int(request.form.get('designversion_id', 0)),  # 提供默认值
        'is_public': request.form.get('is_public', 'false').lower() == 'true'
    }

    # 解析元数据
    parsed_meta = FileParser.parse_file(absolute_storage_path)
    if 'error' in parsed_meta:
        os.remove(absolute_storage_path)
        return jsonify({'error': parsed_meta['error']}), 400

    # 确保只包含 Metadata 模型中定义的字段
    valid_meta_fields = {
        'file_size', 'format', 'mime_type',
        'duration', 'resolution', 'bitrate',
        'page_count', 'word_count', 'author',
        'color_mode', 'dpi', 'extra'
    }
    cleaned_meta = {k: v for k, v in parsed_meta.items() if k in valid_meta_fields}

    # 生成预览图
    try:
        previews = generate_preview(absolute_storage_path, unique_filename)
    except Exception as e:
        current_app.logger.error(f"预览生成失败: {str(e)}")
        previews = {"thumbnail": "/static/default_preview.jpg"}

    # 创建资源文档
    resource = MultimediaResource(
        type=_map_file_type(ext),
        title=form_data['title'],
        description=form_data['description'],
        course_id=form_data['course_id'],
        designversion_id=form_data['designversion_id'],
        uploader_id=get_current_user().id,
        storage_path=relative_storage_path,  # 存储相对路径
        storage_service="local",
        preview_urls=previews,
        metadata=Metadata(**{
            'file_size': os.path.getsize(absolute_storage_path),
            'format': ext.lstrip('.'),
            'mime_type': file.mimetype,
            **cleaned_meta
        }),
        is_public=form_data['is_public']
    )

    try:
        resource.save()
        return jsonify({
            'id': str(resource.id),
            'preview_url': previews.get('thumbnail'),
            'metadata': parsed_meta
        }), 201
    except Exception as e:
        current_app.logger.error(f"保存资源到 MongoDB 时出错: {str(e)}")
        os.remove(absolute_storage_path)  # 删除已保存的文件
        return jsonify({'error': 'Failed to save resource to MongoDB'}), 500

def _map_file_type(ext):
    type_map = {
        'pdf': 'ebook',
        'docx': 'document',
        'pptx': 'presentation',
        'jpg': 'image',
        'png': 'image',
        'mp4': 'video',
        'mp3': 'audio'
    }
    return type_map.get(ext.lstrip('.'), 'other')

@resource_bp.route('/resources/teachingdesignversion/<int:designversion_id>', methods=['GET'])
def get_resources_by_designversion(designversion_id):
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    try:
        # 查询指定教学设计版本的相关资源
        resources = MultimediaResource.objects(designversion_id=designversion_id, uploader_id=current_user.id)

        # 构建响应数据
        resources_data = []
        for resource in resources:
            resource_data = {
                "id": str(resource.id),
                "title": resource.title,
                "designversion_id":resource.designversion_id,
                "description": resource.description,
                "description": resource.description,
                "type": resource.type,
                "storage_path": resource.storage_path,
                "preview_urls": resource.preview_urls,
                "metadata": {
                    "file_size": resource.metadata.file_size,
                    "format": resource.metadata.format,
                    "mime_type": resource.metadata.mime_type,
                    "page_count": resource.metadata.page_count,
                    "word_count": resource.metadata.word_count,
                    "author": resource.metadata.author,
                    "color_mode": resource.metadata.color_mode,
                    "dpi": resource.metadata.dpi,
                    "extra": resource.metadata.extra
                },
                "created_at": resource.created_at.isoformat() if resource.created_at else None,
                "updated_at": resource.updated_at.isoformat() if resource.updated_at else None
            }
            resources_data.append(resource_data)

        return jsonify({"resources": resources_data}), 200

    except Exception as e:
        current_app.logger.error(f"查询资源失败: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@resource_bp.route('/resources', methods=['GET'])
def get_all_resources():
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    try:
        # 查询当前用户的所有资源
        resources = MultimediaResource.objects(uploader_id=current_user.id)

        # 构建响应数据
        resources_data = []
        for resource in resources:
            resource_data = {
                "id": str(resource.id),
                "title": resource.title,
                "course_id":resource.course_id,
                "designversion_id":resource.designversion_id,
                "description": resource.description,
                "type": resource.type,
                "storage_path": resource.storage_path,
                "preview_urls": resource.preview_urls,
                "metadata": {
                    "file_size": resource.metadata.file_size,
                    "format": resource.metadata.format,
                    "mime_type": resource.metadata.mime_type,
                    "page_count": resource.metadata.page_count,
                    "word_count": resource.metadata.word_count,
                    "author": resource.metadata.author,
                    "color_mode": resource.metadata.color_mode,
                    "dpi": resource.metadata.dpi,
                    "extra": resource.metadata.extra
                },
                "created_at": resource.created_at.isoformat() if resource.created_at else None,
                "updated_at": resource.updated_at.isoformat() if resource.updated_at else None
            }
            resources_data.append(resource_data)

        return jsonify({"resources": resources_data}), 200

    except Exception as e:
        current_app.logger.error(f"查询资源失败: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@resource_bp.route('/resources/<resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    # 检查用户是否登录
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    try:
        # 查询指定资源
        resource = MultimediaResource.objects(id=resource_id, uploader_id=current_user.id).first()
        if not resource:
            return jsonify({'error': '资源不存在'}), 404

        # 删除资源文件
        storage_path = os.path.join(project_root, resource.storage_path)
        if os.path.exists(storage_path):
            os.remove(storage_path)

        # 删除资源文档
        resource.delete()

        return jsonify({"message": "资源删除成功"}), 200

    except Exception as e:
        current_app.logger.error(f"删除资源失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@resource_bp.route('/resources/course/<int:course_id>', methods=['GET'])
def get_resources_by_course(course_id):
    try:
        # 查询指定课程的所有资源
        resources = MultimediaResource.objects(course_id=course_id)

        # 构建响应数据
        resources_data = []
        for resource in resources:
            resource_data = {
                "id": str(resource.id),
                "title": resource.title,
                "course_id":resource.course_id,
                "designversion_id":resource.designversion_id,
                "description": resource.description,
                "type": resource.type,
                "storage_path": resource.storage_path,
                "preview_urls": resource.preview_urls,
                "metadata": {
                    "file_size": resource.metadata.file_size,
                    "format": resource.metadata.format,
                    "mime_type": resource.metadata.mime_type,
                    "page_count": resource.metadata.page_count,
                    "word_count": resource.metadata.word_count,
                    "author": resource.metadata.author,
                    "color_mode": resource.metadata.color_mode,
                    "dpi": resource.metadata.dpi,
                    "extra": resource.metadata.extra
                },
                "created_at": resource.created_at.isoformat() if resource.created_at else None,
                "updated_at": resource.updated_at.isoformat() if resource.updated_at else None
            }
            resources_data.append(resource_data)

        return jsonify({"resources": resources_data}), 200

    except Exception as e:
        current_app.logger.error(f"查询课程资源失败: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@resource_bp.route('/resources/<resource_id>', methods=['GET'])
def get_resource_by_id(resource_id):
    try:
        # 查询指定资源
        resource = MultimediaResource.objects(id=resource_id).first()
        if not resource:
            return jsonify({'error': '资源不存在'}), 404

        # 构建响应数据
        resource_data = {
            "id": str(resource.id),
            "title": resource.title,
            "course_id":resource.course_id,
            "designversion_id":resource.designversion_id,
            "description": resource.description,
            "type": resource.type,
            "storage_path": resource.storage_path,
            "preview_urls": resource.preview_urls,
            "metadata": {
                "file_size": resource.metadata.file_size,
                "format": resource.metadata.format,
                "mime_type": resource.metadata.mime_type,
                "page_count": resource.metadata.page_count,
                "word_count": resource.metadata.word_count,
                "author": resource.metadata.author,
                "color_mode": resource.metadata.color_mode,
                "dpi": resource.metadata.dpi,
                "extra": resource.metadata.extra
            },
            "created_at": resource.created_at.isoformat() if resource.created_at else None,
            "updated_at": resource.updated_at.isoformat() if resource.updated_at else None
        }

        return jsonify({"resource": resource_data}), 200

    except Exception as e:
        current_app.logger.error(f"查询单个资源失败: {str(e)}")
        return jsonify({"error": str(e)}), 500
    

@resource_bp.route('/re')
def resourcetemplate():
    return render_template('resource.html')