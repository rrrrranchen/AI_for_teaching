import os
import uuid
from venv import logger
from bson import ObjectId
from flask import Blueprint, app, current_app, redirect, render_template, request, jsonify, send_file, session
from sqlalchemy import func, select
from app.utils.database import db
from app.models.user import User
from app.models.courseclass import Courseclass
from app.models.resources import Metadata, MultimediaResource
from app.models.relationship import teacher_class
from app.utils.file_validators import allowed_file
from app.utils.fileparser import FileParser
from app.utils.secure_filename import secure_filename
from app.utils.preview_generator import generate_preview
from werkzeug.utils import safe_join  
resource_bp=Blueprint('resource',__name__)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(project_root, 'static', 'uploads','techingresources')
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
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file provided"}), 400

    is_allowed, validator = allowed_file(file.filename)
    if not is_allowed:
        return jsonify({"error": "File type not allowed"}), 400

    # 确保上传目录存在
    upload_folder = UPLOAD_FOLDER
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
    storage_path = os.path.join(upload_folder, unique_filename)
    file.save(storage_path)
    
    # 验证文件内容
    if not validator(storage_path):
        os.remove(storage_path)
        return jsonify({"error": "File content does not match extension"}), 400

    # 解析表单数据
    form_data = {
        'title': request.form.get('title', name),
        'description': request.form.get('description', ''),
        'course_id': int(request.form['course_id']),
        'class_ids': list(map(int, request.form.getlist('class_ids'))),
        'is_public': request.form.get('is_public', 'false').lower() == 'true'
    }

    # 解析元数据
    parsed_meta = FileParser.parse_file(storage_path)
    if 'error' in parsed_meta:
        os.remove(storage_path)
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
        previews = generate_preview(storage_path, unique_filename)
    except Exception as e:
        current_app.logger.error(f"预览生成失败: {str(e)}")
        previews = {"thumbnail": "/static/default_preview.jpg"}
    path=os.path.join('static', 'uploads','avatar', unique_filename)
    # 创建资源文档
    resource = MultimediaResource(  # ✅ 不指定_id，使用自动生成的ObjectId
    type=_map_file_type(ext),
    storage_path=path,
    preview_urls=previews,
    metadata=Metadata(**{
        'file_size': os.path.getsize(storage_path),
        'mime_type': file.mimetype,
        **cleaned_meta
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
    type_map = {
        'pdf': 'ebook',
        'docx': 'document',
        'pptx': 'presentation',
        'jpg': 'image',
        'png': 'image',
        'mp4': 'video',
        'mp3': 'audio'
    }
    return type_map.get(ext, 'other')



#查询资源
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
    total = MultimediaResource.objects(**query).count()  # 总记录数
    items = MultimediaResource.objects(**query).skip((page - 1) * per_page).limit(per_page)  # 分页数据

    # 构造分页结果
    pagination = {
        'items': [_format_resource(r) for r in items],
        'total': total,
        'pages': (total + per_page - 1) // per_page,  # 总页数
        'page': page,
        'per_page': per_page
    }

    return jsonify(pagination)

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
                UPLOAD_FOLDER, 
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