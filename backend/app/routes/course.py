from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session
from sqlalchemy import func, select
from app.utils.database import db
from app.models.course import Course
from app.models.courseclass import Courseclass
from app.models.user import User
from app.models.relationship import teacher_class
from app.models.relationship import student_class
course_bp = Blueprint('course', __name__)

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



# 根据 ID 查询单个课程
@course_bp.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        # 获取当前用户
        current_user = get_current_user()

        # 检查当前用户是否为该课程所属课程班的老师或学生
        is_teacher = any(is_teacher_of_courseclass(cc.id) for cc in course.courseclasses)
        is_student = any(
            db.session.scalar(
                select(func.count()).where(
                    student_class.c.student_id == current_user.id,
                    student_class.c.class_id == cc.id
                )
            ) > 0
            for cc in course.courseclasses
        )

        if not is_teacher and not is_student:
            return jsonify({'error': 'You are not authorized to access this course'}), 403

        result = {
            'id': course.id,
            'name': course.name,
            'description': course.description,
            'created_at': course.created_at,
            'courseclasses': [{'id': cc.id, 'name': cc.name} for cc in course.courseclasses],
            'preview_deadline': course.preview_deadline,
            'post_class_deadline': course.post_class_deadline,
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 创建新的课程
@course_bp.route('/courses', methods=['POST'])
def create_course():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description')
        courseclass_ids = data.get('courseclass_ids', [])  # 获取课程班 ID 列表，允许为空

        if not name:
            return jsonify({'error': 'Name is required'}), 400

        # 如果提供了课程班号，检查当前用户是否为所有指定课程班的老师
        if courseclass_ids and not all(is_teacher_of_courseclass(cc_id) for cc_id in courseclass_ids):
            return jsonify({'error': 'You are not authorized to create courses for one or more of the specified course classes'}), 403

        new_course = Course(name=name, description=description)

        # 如果提供了课程班号，则将课程与课程班关联
        if courseclass_ids:
            new_course.courseclasses = Courseclass.query.filter(Courseclass.id.in_(courseclass_ids)).all()

        db.session.add(new_course)
        db.session.commit()

        return jsonify({
            'id': new_course.id,
            'name': new_course.name,
            'description': new_course.description,
            'created_at': new_course.created_at,
            'courseclass_ids': [cc.id for cc in new_course.courseclasses]
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 更新课程信息
@course_bp.route('/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        # 检查当前用户是否为该课程所属课程班的老师
        if not any(is_teacher_of_courseclass(cc.id) for cc in course.courseclasses):
            return jsonify({'error': 'You are not authorized to update this course'}), 403

        data = request.json
        name = data.get('name')
        description = data.get('description')
        courseclass_ids = data.get('courseclass_ids', [])  # 获取课程班 ID 列表

        if name:
            course.name = name
        if description:
            course.description = description

        # 检查当前用户是否为所有指定课程班的老师
        if not all(is_teacher_of_courseclass(cc_id) for cc_id in courseclass_ids):
            return jsonify({'error': 'You are not authorized to update courses for one or more of the specified course classes'}), 403

        course.courseclasses = Courseclass.query.filter(Courseclass.id.in_(courseclass_ids)).all()
        db.session.commit()

        return jsonify({
            'id': course.id,
            'name': course.name,
            'description': course.description,
            'created_at': course.created_at,
            'courseclass_ids': [cc.id for cc in course.courseclasses]
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 删除课程
@course_bp.route('/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        db.session.delete(course)
        db.session.commit()
        return jsonify({'message': 'Course deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# 设置课前习题截止时间
@course_bp.route('/courses/<int:course_id>/set_preview_deadline', methods=['POST'])
def set_preview_deadline(course_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        # 检查当前用户是否为该课程所属课程班的老师
        if not any(is_teacher_of_courseclass(cc.id) for cc in course.courseclasses):
            return jsonify({'error': 'You are not authorized to update this course'}), 403

        data = request.json
        deadline = data.get('deadline')
        if not deadline:
            return jsonify({'error': 'Deadline is required'}), 400

        # 解析截止时间
        try:
            deadline = datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({'error': 'Invalid deadline format. Use YYYY-MM-DD HH:MM:SS'}), 400

        course.preview_deadline = deadline
        db.session.commit()

        return jsonify({'message': 'Preview deadline set successfully', 'deadline': deadline.isoformat()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
# 设置课后习题截止时间
@course_bp.route('/courses/<int:course_id>/set_post_class_deadline', methods=['POST'])
def set_post_class_deadline(course_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        # 检查当前用户是否为该课程所属课程班的老师
        if not any(is_teacher_of_courseclass(cc.id) for cc in course.courseclasses):
            return jsonify({'error': 'You are not authorized to update this course'}), 403

        data = request.json
        deadline = data.get('deadline')
        if not deadline:
            return jsonify({'error': 'Deadline is required'}), 400

        # 解析截止时间
        try:
            deadline = datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return jsonify({'error': 'Invalid deadline format. Use YYYY-MM-DD HH:MM:SS'}), 400

        course.post_class_deadline = deadline
        db.session.commit()

        return jsonify({'message': 'Post-class deadline set successfully', 'deadline': deadline.isoformat()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500