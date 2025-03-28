import os
from venv import logger
from bson import ObjectId
from flask import Blueprint, current_app, redirect, render_template, request, jsonify, send_file, session
from sqlalchemy import func, select
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.question import Question
from app.models.course import Course
from app.services.demo import mock_ai_interface
from app.models.user import User
from app.models.courseclass import Courseclass
from app.models.resources import Metadata, MultimediaResource
from app.models.relationship import teacher_class
from app.utils.file_upload import allowed_file
from app.utils.fileparser import FileParser
from app.utils import secure_filename
from app.utils.preview_generator import generate_preview
from werkzeug.utils import safe_join  # 添加这行导入
resource_bp=Blueprint('resource',__name__)
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
@resource_bp.route('/resources', methods=['POST'])
def upload_resource():
    """文件上传接口"""
    # 1. 验证用户权限
    if not is_logged_in() or get_current_user().role != 'teacher':
        return jsonify({'error': '仅教师可上传资源'}), 403

    # 2. 获取表单数据
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'error': '未选择文件'}), 400

    # 3. 验证文件类型
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 415

    # 4. 解析表单数据
    form_data = {
        'title': request.form.get('title', file.filename.rsplit('.', 1)[0]),
        'description': request.form.get('description', ''),
        'course_id': int(request.form['course_id']),
        'class_ids': list(map(int, request.form.getlist('class_ids'))),
        'is_public': request.form.get('is_public', 'false').lower() == 'true'
    }

    # 5. 保存原始文件
    file_ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    unique_id = str(ObjectId())
    storage_path = os.path.join(
        current_app.config['UPLOAD_FOLDER'],
        f"{unique_id}.{file_ext}"
    )
    file.save(storage_path)

    # 6. 解析元数据
    parsed_meta = FileParser.parse_file(storage_path)
    if 'error' in parsed_meta:
        os.remove(storage_path)
        return jsonify({'error': parsed_meta['error']}), 400

    # 7. 生成预览图
    try:
        previews = generate_preview(storage_path, unique_id)
    except Exception as e:
        current_app.logger.error(f"预览生成失败: {str(e)}")
        previews = {"thumbnail": "/static/default_preview.jpg"}

    # 8. 创建资源文档
    resource = MultimediaResource(
        _id=ObjectId(unique_id),
        type=_map_file_type(file_ext),
        storage_path=storage_path,
        preview_urls=previews,
        metadata=Metadata(**{
            **parsed_meta,
            'mime_type': file.mimetype,
            'file_size': os.path.getsize(storage_path)
        }),
        uploader_id=get_current_user().id,
        **form_data
    )
    resource.save()

    return jsonify({
        'id': str(resource.id),
        'preview_url': previews.get('thumbnail'),
        'metadata': parsed_meta
    }), 201

def _map_file_type(ext):
    """映射文件扩展名到资源类型"""
    type_map = {
        'pdf': 'ebook',
        'pptx': 'presentation',
        'docx': 'document',
        'jpg': 'image',
        'mp4': 'video',
        'mp3': 'audio'
    }
    return type_map.get(ext, 'other')


@resource_bp.route('/resources', methods=['GET'])
def list_resources():
    """分页查询资源"""
    # 1. 获取查询参数
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 10)), 100)
    course_id = request.args.get('course_id')
    class_id = request.args.get('class_id')
    resource_type = request.args.get('type')

    # 2. 构建查询条件
    query = {}
    if course_id:
        query['course_id'] = int(course_id)
    if class_id:
        query['class_ids'] = int(class_id)
    if resource_type:
        query['type'] = resource_type

    # 3. 执行分页查询
    pagination = MultimediaResource.objects(**query).paginate(
        page=page, 
        per_page=per_page
    )

    return jsonify({
        'items': [_format_resource(r) for r in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    })

def _format_resource(resource):
    """格式化资源输出"""
    return {
        'id': str(resource.id),
        'title': resource.title,
        'type': resource.type,
        'preview_url': resource.preview_urls.get('thumbnail'),
        'course_id': resource.course_id,
        'uploader_id': resource.uploader_id,
        'created_at': resource.created_at.isoformat(),
        'metadata': {
            'duration': resource.metadata.duration,
            'page_count': resource.metadata.page_count,
            'file_size': resource.metadata.file_size
        }
    }


@resource_bp.route('/resources/<resource_id>', methods=['GET'])
def get_resource(resource_id):
    """获取资源详情"""
    try:
        resource = MultimediaResource.objects.get(id=resource_id)
        if not _check_resource_access(resource):
            return jsonify({'error': '无权访问该资源'}), 403

        return jsonify(_format_resource_detail(resource))
    except:
        return jsonify({'error': '资源不存在'}), 404

def _format_resource_detail(resource):
    """格式化详情输出"""
    base = _format_resource(resource)
    base.update({
        'description': resource.description,
        'download_url': resource.get_download_url(),
        'is_public': resource.is_public,
        'class_ids': resource.class_ids,
        'metadata': {
            **base['metadata'],
            'resolution': resource.metadata.resolution,
            'author': resource.metadata.author,
            'format': resource.metadata.format
        }
    })
    return base

def _check_resource_access(resource):
    """检查资源访问权限"""
    user = get_current_user()
    if resource.is_public:
        return True
    if not user:
        return False
    if user.role == 'admin':
        return True
    if user.id == resource.uploader_id:
        return True
    if set(resource.class_ids) & set(c.id for c in user.student_courseclasses):
        return True
    return False


@resource_bp.route('/resources/<resource_id>/download', methods=['GET'])
def download_resource(resource_id):
    """文件下载接口"""
    try:
        resource = MultimediaResource.objects.get(id=resource_id)
        if not _check_resource_access(resource):
            return jsonify({'error': '无权下载该资源'}), 403

        if resource.storage_service == 'local':
            # 使用 werkzeug 的 safe_join 确保路径安全
            file_path = safe_join(
                current_app.config['UPLOAD_FOLDER'], 
                os.path.basename(resource.storage_path)  # 防止路径遍历
            )
            
            if not os.path.exists(file_path):
                return jsonify({'error': '文件不存在'}), 404
                
            return send_file(
                file_path,
                as_attachment=True,
                mimetype=resource.metadata.mime_type,
                download_name=secure_filename(resource.title) + f".{resource.metadata.format}"
            )
        else:
            return redirect(resource.get_download_url())
    except Exception as e:
        current_app.logger.error(f"下载失败: {str(e)}")
        return jsonify({'error': '文件下载出错'}), 500
    
@resource_bp.route('/re')
def resourcetemplate():
    return render_template('resource.html')