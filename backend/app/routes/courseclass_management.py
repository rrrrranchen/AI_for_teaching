from flask import Blueprint, g, jsonify, request, session
from app.utils.database import db
from app.models.user import User
from app.models.courseclass import Courseclass
from app.models.course import Course
from app.routes.courseclass import generate_invite_code
from app.utils.file_upload import upload_file_courseclass

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
    data = request.get_json()
    
    # 获取筛选条件
    name = data.get('name', None)  # 课程班名称筛选
    teacher_id = data.get('teacher_id', None)  # 教师ID筛选
    student_id = data.get('student_id', None)  # 学生ID筛选
    course_id = data.get('course_id', None)  # 课程ID筛选
    invite_code = data.get('invite_code', None)  # 邀请码筛选

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
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404

        # 获取请求数据
        data = request.form
        name = data.get('name')
        description = data.get('description')
        image_file = request.files.get('image')  # 获取上传的图片文件

        # 更新课程班信息
        if name:
            courseclass.name = name
        if description:
            courseclass.description = description

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

