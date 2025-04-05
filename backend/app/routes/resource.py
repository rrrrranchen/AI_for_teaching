from datetime import datetime
import os
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
from app.utils.secure_filename import secure_filename
from app.utils.preview_generator import generate_preview
from werkzeug.utils import safe_join  
from mongoengine.errors import DoesNotExist, ValidationError

from app.services.ai_service import generate_PPT
from app.models.ppttemplate import PPTTemplate
from app.models.teachingdesignversion import TeachingDesignVersion
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


@resource_bp.route('/createPPT/<int:course_id>/<int:teachingdesignversion_id>/<int:ppttemplate_id>')
def generatePPT(course_id, teachingdesignversion_id, ppttemplate_id):
    # 查询教学设计版本
    teaching_design_version = TeachingDesignVersion.query.filter_by(
        id=teachingdesignversion_id
    ).first()
    
    if not teaching_design_version:
        return jsonify({"error": "Teaching design version not found"}), 404

    # 获取教学设计内容
    teaching_plan = teaching_design_version.content

    # 查询 PPT 模板
    ppt_template = PPTTemplate.query.filter_by(id=ppttemplate_id).first()
    if not ppt_template:
        return jsonify({"error": "PPT template not found"}), 404

    # 获取模板路径
    template_path = ppt_template.url

    # 从请求中获取标题
    title = request.args.get('title', default="教学设计 PPT", type=str)  # 从 URL 查询参数获取
    # 如果需要从表单数据获取，可以使用 request.form.get('title', default="教学设计 PPT")

    # 生成 PPT
    storage_path = generate_PPT(
        teaching_plan=teaching_plan,
        teacher_name="AI",
        time=datetime.utcnow().strftime("%Y/%m/%d"),
        template=template_path,  
        ppt_filename=None,
        select='plan'
    )

    # 生成唯一的文件名
    unique_filename = str(uuid.uuid4()) + ".pptx"
    final_storage_path = os.path.join("static", "uploads", "teachingresources", unique_filename)

    # 将 PPT 文件移动到最终存储路径
    os.rename(storage_path, final_storage_path)

    # 生成元数据
    parsed_meta = FileParser.parse_file(final_storage_path)
    if 'error' in parsed_meta:
        os.remove(final_storage_path)
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
        previews = generate_preview(final_storage_path, unique_filename)
    except Exception as e:
        current_app.logger.error(f"预览生成失败: {str(e)}")
        previews = {"thumbnail": "/static/default_preview.jpg"}

    # 创建资源文档
    resource = MultimediaResource(
        type="presentation",  # PPT 类型
        title=title,  # 使用前端提供的标题
        description="自动生成的教学设计 PPT",
        course_id=course_id,
        designversion_id=teachingdesignversion_id,
        uploader_id=get_current_user().id,
        storage_path=final_storage_path,
        preview_urls=previews,
        metadata=Metadata(**{
            'file_size': os.path.getsize(final_storage_path),
            'mime_type': "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            **cleaned_meta
        }),
        is_teaching_design=True  # 标记为教学设计 PPT
    )
    resource.save()

    return jsonify({
        'id': str(resource.id),
        'preview_url': previews.get('thumbnail'),
        'metadata': parsed_meta,
        'message': "PPT generated and stored successfully"
    }), 201


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
        'designversion_id': int(request.form['designversion_id']),  # 新增字段
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

    # 创建资源文档
    resource = MultimediaResource(
        type=_map_file_type(ext),
        storage_path=os.path.join('static', 'uploads', 'teachingresources', unique_filename),
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

    print("Query:", query)

    # 3. 执行分页查询
    total = MultimediaResource.objects(**query).count()  # 总记录数
    print("Total records:", total)
    items = MultimediaResource.objects(**query).skip((page - 1) * per_page).limit(per_page)  # 分页数据
    print("Items:", items)

    # 构造分页结果
    pagination = {
        'items': [_format_resource(r) for r in items if _format_resource(r) is not None],
        'total': total,
        'pages': (total + per_page - 1) // per_page,  # 总页数
        'page': page,
        'per_page': per_page
    }

    if page > pagination['pages']:
        pagination['items'] = []
        print(f"Warning: Requested page {page} exceeds the total number of pages ({pagination['pages']}).")

    print("Pagination:", pagination)
    return jsonify(pagination)

def _format_resource(resource):
    try:
        return {
            'id': str(resource.id),
            'title': resource.title,
            'type': resource.type,
            'preview_url': resource.preview_urls.get('thumbnail'),
            'course_id': resource.course_id,
            'uploader_id': resource.uploader_id,
            'created_at': resource.created_at.isoformat(),
            'metadata': {
                'duration': getattr(resource.metadata, 'duration', None),
                'page_count': getattr(resource.metadata, 'page_count', None),
                'file_size': getattr(resource.metadata, 'file_size', None)
            }
        }
    except Exception as e:
        print(f"Error formatting resource {resource.id}: {e}")
        return None

@resource_bp.route('/resources/<resource_id>', methods=['GET'])
def get_resource(resource_id):
    """获取资源详情（修正版）"""
    # 生成唯一请求ID
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] 资源详情请求: {resource_id}")

    try:
        # 验证ObjectID格式
        obj_id = ObjectId(resource_id)
    except Exception as e:
        logger.warning(f"[{request_id}] 无效的ObjectID: {resource_id} - {str(e)}")
        return jsonify({
            'error': '资源ID格式错误',
            'valid_example': '507f1f77bcf86cd799439011',
            'request_id': request_id
        }), 400

    try:
        # 修正查询字段：使用 _id 替代 id
        resource = MultimediaResource.objects.get(_id=obj_id)
        
        # 权限验证
        if not _check_resource_access(resource):
            logger.info(f"[{request_id}] 访问被拒绝: {resource_id}")
            return jsonify({
                'error': '无访问权限',
                'required_conditions': [
                    '资源已公开 或',
                    '您是上传者 或',
                    '属于关联班级'
                ],
                'request_id': request_id
            }), 403

        logger.debug(f"[{request_id}] 资源查询成功: {resource_id}")
        return jsonify(_format_resource_detail(resource))

    except DoesNotExist:
        logger.warning(f"[{request_id}] 资源不存在: {resource_id}")
        return jsonify({
            'error': '资源不存在',
            'check_suggestion': [
                '确认资源ID是否正确',
                '检查资源是否已被删除'
            ],
            'request_id': request_id
        }), 404
        
    except (ValidationError, InvalidKeyError) as e:
        logger.error(f"[{request_id}] 查询错误: {str(e)}")
        return jsonify({
            'error': '查询参数验证失败',
            'technical_info': '请检查资源ID格式',
            'request_id': request_id
        }), 400
        
    except Exception as e:
        logger.error(f"[{request_id}] 服务器错误: {str(e)}", exc_info=True)
        return jsonify({
            'error': '服务器内部错误',
            'request_id': request_id
        }), 500

def _check_resource_access(resource):
    """增强版权限验证"""
    user = get_current_user()
    
    # 公开资源允许访问
    if resource.is_public:
        return True
    
    # 未登录用户拒绝访问
    if not user:
        return False
    
    # 上传者允许访问
    if hasattr(user, 'id') and user.id == resource.uploader_id:
        return True
    
    # 检查用户是否在关联班级中
    if (hasattr(user, 'class_ids') and 
        set(user.class_ids) & set(resource.class_ids)):
        return True
    
    return False
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