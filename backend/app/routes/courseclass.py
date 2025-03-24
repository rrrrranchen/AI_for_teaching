from flask import Blueprint, render_template, request, jsonify, session
from pymysql import IntegrityError
from sqlalchemy import func, select
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.courseclass import Courseclass
from app.models.course import Course
from app.models.user import User
from app.models.relationship import teacher_class,student_class,course_courseclass
courseclass_bp = Blueprint('courseclass', __name__)

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

#查询所有课程班
@courseclass_bp.route('/courseclasses', methods=['GET'])
def get_courseclasses():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        # 获取当前登录用户
        current_user = get_current_user()
        if not current_user or current_user.role != 'teacher':
            return jsonify({'error': 'Only teachers can access course classes'}), 403

        # 查询当前老师的所有课程班
        courseclasses = Courseclass.query.join(teacher_class).filter(teacher_class.c.teacher_id == current_user.id).all()

        result = [
            {
                'id': courseclass.id,
                'name': courseclass.name,
                'description': courseclass.description,
                'created_at': courseclass.created_at,
                'courses': [{'id': course.id, 'name': course.name} for course in courseclass.courses]
            }
            for courseclass in courseclasses
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 根据 ID 查询单个课程班
@courseclass_bp.route('/courseclasses/<int:courseclass_id>', methods=['GET'])
def get_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        # 检查当前用户是否为该课程班的老师
        if not is_teacher_of_courseclass(courseclass_id):
            return jsonify({'error': 'You are not authorized to access this course class'}), 403

        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404

        result = {
            'id': courseclass.id,
            'name': courseclass.name,
            'description': courseclass.description,
            'created_at': courseclass.created_at,
            'courses': [{'id': course.id, 'name': course.name} for course in courseclass.courses]
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#创建课程班
@courseclass_bp.route('/createcourseclasses', methods=['POST'])
def create_courseclass():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 获取当前登录用户
        current_user = get_current_user()
        if not current_user or current_user.role != 'teacher':
            return jsonify({'error': 'Only teachers can create course classes'}), 403

        # 获取请求数据
        data = request.json
        name = data.get('name')
        description = data.get('description')

        if not name:
            return jsonify({'error': 'Name is required'}), 400

        # 创建新的课程班
        new_courseclass = Courseclass(name=name, description=description)
        db.session.add(new_courseclass)
        db.session.flush()  # 获取 new_courseclass.id

        # 插入关联
        db.session.execute(
            teacher_class.insert().values(
                teacher_id=current_user.id,
                class_id=new_courseclass.id
            )
        )
        db.session.commit()

        return jsonify({
            'id': new_courseclass.id,
            'name': new_courseclass.name,
            'description': new_courseclass.description,
            'created_at': new_courseclass.created_at
        }), 201
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'error': 'This teacher is already associated with the course class'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# 更新课程班信息
@courseclass_bp.route('/courseclasses/<int:courseclass_id>', methods=['PUT'])
def update_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        # 检查当前用户是否为该课程班的老师
        if not is_teacher_of_courseclass(courseclass_id):
            return jsonify({'error': 'You are not authorized to update this course class'}), 403

        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404

        data = request.json
        name = data.get('name')
        description = data.get('description')

        if name:
            courseclass.name = name
        if description:
            courseclass.description = description
        db.session.commit()

        return jsonify({
            'id': courseclass.id,
            'name': courseclass.name,
            'description': courseclass.description,
            'created_at': courseclass.created_at
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

#删除单个课程班
@courseclass_bp.route('/deletecourseclasses/<int:courseclass_id>', methods=['DELETE'])
def delete_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 检查当前用户是否为该课程班的老师
        if not is_teacher_of_courseclass(courseclass_id):
            return jsonify({'error': 'You are not authorized to delete this course class'}), 403

        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404

        # 删除课程班（自动级联删除关联表中的数据）
        db.session.delete(courseclass)
        db.session.commit()

        return jsonify({'message': 'CourseClass deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 为课程班添加课程
@courseclass_bp.route('/courseclasses/<int:courseclass_id>/add_courses', methods=['POST'])
def add_courses_to_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        # 检查当前用户是否为该课程班的老师
        if not is_teacher_of_courseclass(courseclass_id):
            return jsonify({'error': 'You are not authorized to add courses to this course class'}), 403

        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404

        data = request.json
        course_ids = data.get('course_ids')
        if not course_ids:
            return jsonify({'error': 'Course IDs are required'}), 400

        # 查询所有指定的课程
        courses = Course.query.filter(Course.id.in_(course_ids)).all()
        if len(courses) != len(course_ids):
            return jsonify({'error': 'One or more courses not found'}), 404

        # 将课程添加到课程班
        for course in courses:
            if course not in courseclass.courses:
                courseclass.courses.append(course)

        db.session.commit()
        return jsonify({'message': 'Courses added to CourseClass successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


#为课程班删除课程
@courseclass_bp.route('/courseclasses/<int:courseclass_id>/remove_courses', methods=['POST'])
def remove_courses_from_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        # 检查当前用户是否为该课程班的老师
        if not is_teacher_of_courseclass(courseclass_id):
            return jsonify({'error': 'You are not authorized to remove courses from this course class'}), 403

        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404

        data = request.json
        course_ids = data.get('course_ids')
        if not course_ids:
            return jsonify({'error': 'Course IDs are required'}), 400

        # 查询所有指定的课程
        courses = Course.query.filter(Course.id.in_(course_ids)).all()
        if len(courses) != len(course_ids):
            return jsonify({'error': 'One or more courses not found'}), 404

        # 删除课程与课程班的关联
        for course in courses:
            if course in courseclass.courses:
                courseclass.courses.remove(course)

                # 检查课程是否还关联其他课程班
                remaining_courseclasses = Courseclass.query.join(course_courseclass).filter(course_courseclass.c.course_id == course.id).all()
                if not remaining_courseclasses:
                    # 如果没有关联其他课程班，则删除课程
                    db.session.delete(course)

        db.session.commit()
        return jsonify({'message': 'Courses removed from CourseClass successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 根据课程班 ID 查找所有所属课程班的课程
@courseclass_bp.route('/courseclasses/<int:courseclass_id>/courses', methods=['GET'])
def get_courses_by_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        # 检查当前用户是否为该课程班的老师
        if not is_teacher_of_courseclass(courseclass_id):
            return jsonify({'error': 'You are not authorized to access courses of this course class'}), 403

        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404

        courses = courseclass.courses

        result = [
            {
                'id': course.id,
                'name': course.name,
                'description': course.description
            }
            for course in courses
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courseclass_bp.route('/courseclass')
def courseclasspage():
    return render_template('courseclass.html')