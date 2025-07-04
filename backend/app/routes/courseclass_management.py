from datetime import datetime
from flask import Blueprint, g, jsonify, request, session
from sqlalchemy import func
from app.utils.database import db
from app.models.user import User
from app.models.courseclass import Courseclass
from app.models.course import Course
from app.routes.courseclass import generate_invite_code
from app.utils.file_upload import upload_file_courseclass
from app.services.rank import generate_public_courseclass_ranking
from app.services.log_service import LogService
from app.models.CourseClassApplication import CourseClassApplication

courseclass_management_bp = Blueprint('courseclass_management', __name__)

def is_logged_in():
    return 'user_id' in session

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

@courseclass_management_bp.before_request
def before_request():
    # 检查用户是否已登录
    if request.method == 'OPTIONS':
        return
    if is_logged_in():
        # 获取当前用户并存储到 g 对象中
        g.current_user = get_current_user()
        # 检查用户是否为管理员
        if g.current_user and g.current_user.role != 'admin':
            return jsonify({'error': 'Forbidden'}), 403
    else:
        # 如果用户未登录，返回未授权错误
        return jsonify({'error': 'Unauthorized'}), 401
    

@courseclass_management_bp.route('/admin/query_courseclasses', methods=['GET'])
def query_courseclasses():
    
    # 获取筛选条件
    name = request.args.get('name', None)  # 课程班名称筛选
    teacher_id = request.args.get('teacher_id', None)  # 教师ID筛选
    student_id = request.args.get('student_id', None)  # 学生ID筛选
    course_id = request.args.get('course_id', None)  # 课程ID筛选
    invite_code = request.args.get('invite_code', None)  # 邀请码筛选

    # 基础查询
    query = Courseclass.query

    # 根据课程班名称筛选（模糊匹配）
    if name:
        query = query.filter(Courseclass.name.like(f'%{name}%'))

    # 根据教师ID筛选
    if teacher_id:
        query = query.join(Courseclass.teachers).filter(User.id == teacher_id)

    # 根据学生ID筛选
    if student_id:
        query = query.join(Courseclass.students).filter(User.id == student_id)

    # 根据课程ID筛选
    if course_id:
        query = query.join(Courseclass.courses).filter(Course.id == course_id)

    # 根据邀请码筛选（精确匹配）
    if invite_code:
        query = query.filter(Courseclass.invite_code == invite_code)

    # 按创建时间降序排序
    query = query.order_by(Courseclass.created_at.desc())

    # 获取查询结果
    courseclasses = query.all()

    # 构造返回数据
    courseclass_list = []
    for cc in courseclasses:
        courseclass_data = {
            'id': cc.id,
            'name': cc.name,
            'description': cc.description,
            'created_at': cc.created_at.isoformat(),
            'invite_code': cc.invite_code,
            'image_path': cc.image_path,
            'is_public': cc.is_public,
            'teacher_count': len(cc.teachers),
            'student_count': len(cc.students),
            'course_count': len(cc.courses),
            # 可选：包含部分关联信息
            'teachers': [{'id': t.id, 'name': t.username} for t in cc.teachers][:3],  # 只显示前3个教师
            'courses': [{'id': c.id, 'name': c.name} for c in cc.courses][:3]  # 只显示前3个课程
        }
        courseclass_list.append(courseclass_data)

    return jsonify(courseclass_list), 200


@courseclass_management_bp.route('/admin/update_courseclass/<int:courseclass_id>', methods=['PUT'])
def update_courseclass(courseclass_id):
    try:
        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404

        # 获取请求数据
        data = request.form
        name = data.get('name')
        description = data.get('description')
        is_public=data.get('is_public')
        image_file = request.files.get('image')  # 获取上传的图片文件

        # 更新课程班信息
        if name:
            courseclass.name = name
        if description:
            courseclass.description = description
        #确认公开状态
        if is_public is not None:
            courseclass.is_public = is_public.lower() == 'true' if isinstance(is_public, str) else bool(is_public)

        # 更新图片
        if image_file:
            image_path = upload_file_courseclass(image_file)
            courseclass.image_path = image_path
        else:
            # 如果没有上传新图片，保持原图片路径
            pass

        db.session.commit()

        return jsonify({
            'id': courseclass.id,
            'name': courseclass.name,
            'description': courseclass.description,
            'created_at': courseclass.created_at,
            'is_public': courseclass.is_public,
            'image_path': courseclass.image_path  # 返回更新后的图片路径
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@courseclass_management_bp.route('/admin/delete_courseclasses', methods=['DELETE'])
def delete_courseclasses():
    """批量删除课程班"""
    data = request.get_json()
    courseclass_ids = data.get('courseclass_ids', [])

    if not courseclass_ids:
        return jsonify({'message': 'No course class IDs provided'}), 400

    # 查询所有要删除的课程班
    courseclasses = Courseclass.query.filter(Courseclass.id.in_(courseclass_ids)).all()

    # 删除每个课程班及其关联关系
    for courseclass in courseclasses:
        # 先删除关联关系
        courseclass.teachers = []
        courseclass.students = []
        courseclass.courses = []

    # 批量删除课程班
    Courseclass.query.filter(Courseclass.id.in_(courseclass_ids)).delete()

    # 提交事务
    db.session.commit()

    return jsonify({'message': 'Course classes deleted successfully'}), 200

@courseclass_management_bp.route('/public_courseclass_ranking', methods=['GET'])
def get_public_courseclass_ranking():
    """
    获取公开课程班排行榜
    返回前10个推荐指数最高的公开课程班
    """
    try:
        # 获取所有公开课程班并按推荐指数排序
        public_classes = Courseclass.query.filter_by(is_public=True).all()
        
        if not public_classes:
            return jsonify([]), 200
        
        # 获取排行榜数据
        ranking = generate_public_courseclass_ranking()
        
        # 只取前10名
        top_10 = ranking[:10]
        
        # 构造返回数据
        result = []
        for rank, courseclass in enumerate(top_10, start=1):
            # 获取课程班详细信息
            cc = Courseclass.query.get(courseclass['class_id'])
            
            result.append({
                'rank': rank,
                'id': cc.id,
                'name': cc.name,
                'description': cc.description[:100] + "..." if cc.description else "",
                'image_path': cc.image_path,
                'invite_code': cc.invite_code,
                'recommend_index': round(courseclass['recommend_index'], 1),
                'stars': courseclass['stars'],
                'student_count': courseclass['student_count'],
                'teacher_count': courseclass['teacher_count'],
                'course_count': courseclass['course_count'],
                'avg_accuracy': round(courseclass['avg_accuracy'], 1),
                'activity_ratio': round(courseclass['activity_ratio'], 1)
            })
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# 基于学生已加入的课程和热门程度推荐课程
@courseclass_management_bp.route('/courseclass/recommend_courseclasses', methods=['GET'])
def recommend_courseclasses():
    try:
        if not is_logged_in():
            return jsonify({'error': 'Unauthorized'}), 401

        current_user = g.current_user
        limit = int(request.args.get('limit', 5))  # 默认返回10个推荐

        # 获取学生已加入的课程班
        joined_classes = current_user.student_courseclasses
        joined_class_ids = [cc.id for cc in joined_classes]
        
        # 1. 基于已学课程的推荐
        recommended_by_courses = []
        
        # 获取学生已学习的课程ID
        learned_course_ids = set()
        for cc in joined_classes:
            for course in cc.courses:
                learned_course_ids.add(course.id)

        if learned_course_ids:
            # 查找包含这些课程的公开课程班
            recommended_by_courses = Courseclass.query \
                .join(Courseclass.courses) \
                .filter(
                    Courseclass.is_public == True,
                    Course.id.in_(list(learned_course_ids)),
                    ~Courseclass.id.in_(joined_class_ids)  # 排除已加入的
                ) \
                .group_by(Courseclass.id) \
                .order_by(func.count(Course.id).desc()) \
                .limit(limit) \
                .all()

        # 2. 基于热度的推荐(从排行榜获取)
        ranking = generate_public_courseclass_ranking()
        hot_recommendations = []
        
        for item in ranking:
            if len(hot_recommendations) >= limit:
                break
            cc = Courseclass.query.get(item['class_id'])
            if cc and cc.id not in joined_class_ids:
                hot_recommendations.append(cc)

        # 合并推荐结果并去重
        all_recommendations = recommended_by_courses + hot_recommendations
        unique_recommendations = []
        seen_ids = set()
        
        for cc in all_recommendations:
            if cc.id not in seen_ids:
                seen_ids.add(cc.id)
                unique_recommendations.append(cc)
                if len(unique_recommendations) >= limit:
                    break

        # 构造返回数据
        result = []
        for cc in unique_recommendations[:limit]:
            # 计算推荐理由
            reason = "热门课程班" if cc in hot_recommendations else "基于您已学习的课程"
            
            # 获取课程班的基本信息
            cc_data = {
                'id': cc.id,
                'name': cc.name,
                'description': cc.description[:100] + "..." if cc.description else "",
                'image_path': cc.image_path,
                'invite_code': cc.invite_code,
                'is_public': cc.is_public,
                'reason': reason,
                'teacher_count': len(cc.teachers),
                'student_count': len(cc.students),
                'course_count': len(cc.courses),
                'courses': [{'id': c.id, 'name': c.name} for c in cc.courses][:3]
            }
            result.append(cc_data)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



# 申请课程班
@courseclass_management_bp.route('/courseclass/<int:courseclass_id>/apply', methods=['POST'])
def apply_to_courseclass(courseclass_id):
    try:
        if not is_logged_in():
            return jsonify({'error': 'Unauthorized'}), 401

        courseclass = Courseclass.query.get_or_404(courseclass_id)
        current_user = g.current_user

        # 检查是否已经是成员
        if current_user in courseclass.students:
            return jsonify({'error': '您已经是该课程班成员'}), 400

        # 检查是否已有待处理申请
        existing = CourseClassApplication.query.filter_by(
            student_id=current_user.id,
            courseclass_id=courseclass_id,
            status='pending'
        ).first()

        if existing:
            return jsonify({'error': '您已提交过申请，请等待处理'}), 400


        if not courseclass.teachers:
            return jsonify({'error': '该课程班暂无教师，无法提交申请'}), 400
            
        first_teacher = courseclass.teachers[0]
        # 创建新申请
        data = request.get_json()
        application = CourseClassApplication(
            student_id=current_user.id,
            teacher_id=first_teacher.id,
            courseclass_id=courseclass_id,
            application_date=datetime.utcnow(),
            message=data.get('message', ''),
            status='pending'
        )

        db.session.add(application)
        db.session.commit()

        return jsonify({
            'message': f'申请已提交至教师 {first_teacher.username}',
            'application_id': application.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 查看申请状况
@courseclass_management_bp.route('/courseclass/<int:courseclass_id>/applications', methods=['GET'])
def get_courseclass_applications(courseclass_id):
    try:
        if not is_logged_in():
            return jsonify({'error': 'Unauthorized'}), 401

        courseclass = Courseclass.query.get_or_404(courseclass_id)
        current_user = g.current_user

        # 验证教师权限
        if current_user not in courseclass.teachers and current_user.role != 'admin':
            return jsonify({'error': '无权访问此课程班的申请'}), 403

        # 获取筛选条件
        status = request.args.get('status', None)
        
        query = CourseClassApplication.query.filter_by(
            courseclass_id=courseclass_id
        )

        if status:
            query = query.filter_by(status=status)

        applications = query.order_by(CourseClassApplication.application_date.desc()).all()

        result = [{
            'id': app.id,
            'student_id': app.student.id,
            'student_name': app.student.username,
            'status': app.status,
            'application_date': app.application_date.isoformat(),
            'processed_date': app.processed_date.isoformat() if app.processed_date else None,
            'message': app.message,
            'admin_notes': app.admin_notes
        } for app in applications]

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courseclass_management_bp.route('/courseclass/applications/<int:application_id>/process', methods=['POST'])
def process_application(application_id):
    try:
        if not is_logged_in():
            return jsonify({'error': 'Unauthorized'}), 401

        application = CourseClassApplication.query.get_or_404(application_id)
        courseclass = application.courseclass
        current_user = g.current_user

        # 验证教师权限
        if current_user not in courseclass.teachers and current_user.role != 'admin':
            return jsonify({'error': '无权处理此申请'}), 403

        # 如果已经处理过
        if application.status != 'pending':
            return jsonify({'error': '该申请已处理'}), 400

        data = request.get_json()
        action = data.get('action')
        admin_notes = data.get('admin_notes', '')

        if action not in ['approve', 'reject']:
            return jsonify({'error': '无效的操作类型'}), 400

        # 处理申请
        if action == 'approve':
            # 添加学生到课程班
            if application.student not in courseclass.students:
                courseclass.students.append(application.student)
            application.status = 'approved'
            message = '已批准申请'
        else:
            application.status = 'rejected'
            message = '已拒绝申请'

        # 更新公共字段
        application.admin_notes = admin_notes
        application.processed_date = datetime.utcnow()
        application.teacher_id = current_user.id

        db.session.commit()

        return jsonify({
            'message': message,
            'application_id': application.id,
            'status': application.status
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@courseclass_management_bp.route('/courseclass/my_applications', methods=['GET'])
def get_my_applications():
    try:
        if not is_logged_in():
            return jsonify({'error': 'Unauthorized'}), 401

        current_user = g.current_user
        
        # 获取筛选条件
        status = request.args.get('status', None)
        
        query = CourseClassApplication.query.filter_by(
            student_id=current_user.id
        )

        if status:
            query = query.filter_by(status=status)

        applications = query.order_by(CourseClassApplication.application_date.desc()).all()

        result = [{
            'id': app.id,
            'courseclass_id': app.courseclass.id,
            'courseclass_name': app.courseclass.name,
            'status': app.status,
            'application_date': app.application_date.isoformat(),
            'processed_date': app.processed_date.isoformat() if app.processed_date else None,
            'message': app.message,
            'admin_notes': app.admin_notes
        } for app in applications]

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courseclass_management_bp.after_request
def log_after_request(response):
    # 跳过预检请求和错误响应
    if request.method == 'OPTIONS' or not (200 <= response.status_code < 400):
        return response

    # 获取当前用户（已通过before_request验证）
    current_user = g.current_user
    user_info = {
        'id': current_user.id,
        'role': current_user.role
    }

    # 记录所有成功请求（无需白名单检查）
    LogService.log_operation(
        user_id=user_info['id'],
        user_type=user_info['role'],
        operation_type=f"{request.method}_{request.endpoint.replace('.', '_')}",
        details={
            'path': request.path,
            'method': request.method,
            'params': dict(request.args) if request.args else None,
            'body': request.get_json(silent=True) if request.method in ['POST', 'PUT', 'PATCH'] else None,
            'status': response.status_code,
            'timestamp': datetime.now().isoformat()
        }
    )
    return response