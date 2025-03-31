import random
import string
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

# 生成固定长度的邀请码
def generate_invite_code(length=20):
    characters = string.ascii_letters + string.digits
    invite_code = ''.join(random.choice(characters) for _ in range(length))
    return invite_code

# 查询用户的所有课程班
@courseclass_bp.route('/courseclasses', methods=['GET'])
def get_courseclasses():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 获取当前登录用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # 根据用户角色进行不同的查询
        if current_user.role == 'teacher':
            # 查询当前老师的所有课程班
            courseclasses = Courseclass.query.options(
                db.joinedload(Courseclass.teachers)
            ).join(teacher_class).filter(teacher_class.c.teacher_id == current_user.id).all()
        elif current_user.role == 'student':
            # 查询当前学生所属的所有课程班
            courseclasses = current_user.student_courseclasses.all()
        else:
            return jsonify({'error': 'Invalid user role'}), 403

        result = [
            {
                'id': courseclass.id,
                'name': courseclass.name,
                'description': courseclass.description,
                'created_at': courseclass.created_at,
                'invite_code': courseclass.invite_code,  # 返回邀请码
                'teachers': [
                {'id': teacher.id, 'username': teacher.username}
                for teacher in courseclass.teachers
            ]
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
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # 检查当前用户是否为该课程班的老师或学生
        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404

        # 检查用户是否为该课程班的老师或学生
        if not is_teacher_of_courseclass(courseclass_id) and current_user not in courseclass.students:
            return jsonify({'error': 'You are not authorized to access this course class'}), 403

        result = {
            'id': courseclass.id,
            'name': courseclass.name,
            'description': courseclass.description,
            'created_at': courseclass.created_at,
            'invite_code': courseclass.invite_code,  # 返回邀请码
            'courses': [{'id': course.id, 'name': course.name} for course in courseclass.courses],
            'teachers': [
                {'id': teacher.id, 'username': teacher.username}
                for teacher in courseclass.teachers
            ]
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 创建课程班
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

        # 生成邀请码
        invite_code = generate_invite_code()

        # 创建新的课程班
        new_courseclass = Courseclass(name=name, description=description, invite_code=invite_code)
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
            'created_at': new_courseclass.created_at,
            'invite_code': new_courseclass.invite_code  # 返回邀请码
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
            return jsonify({'error': 'You are not authorized to access students of this course class'}), 403

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
    


@courseclass_bp.route('/student_join_courseclass', methods=['POST'])
def student_join_courseclass():
    if not is_logged_in():
        return jsonify({"error": "User is not logged in"}), 401

    data = request.json
    invite_code = data.get('invite_code')  # 获取邀请码

    if not invite_code:
        return jsonify({"error": "Missing invite_code"}), 400

    current_user = get_current_user()
    if not current_user or current_user.role != 'student':
        return jsonify({"error": "User is not a student"}), 403

    # 根据邀请码查询课程班
    courseclass = Courseclass.query.filter_by(invite_code=invite_code).first()
    if not courseclass:
        return jsonify({"error": "Course class not found or invalid invite code"}), 404

    # 检查学生是否已经加入了该课程班
    if current_user in courseclass.students:
        return jsonify({"error": "Student is already in this course class"}), 400

    # 将学生添加到课程班
    courseclass.students.append(current_user)
    db.session.commit()

    return jsonify({"message": "Student joined the course class successfully"}), 200

@courseclass_bp.route('/student_leave_courseclass', methods=['POST'])
def student_leave_courseclass():
    if not is_logged_in():
        return jsonify({"error": "User is not logged in"}), 401

    data = request.json
    courseclass_id = data.get('courseclass_id')

    if not courseclass_id:
        return jsonify({"error": "Missing courseclass_id"}), 400

    current_user = get_current_user()
    if not current_user or current_user.role != 'student':
        return jsonify({"error": "User is not a student"}), 403

    courseclass = Courseclass.query.get(courseclass_id)
    if not courseclass:
        return jsonify({"error": "Course class not found"}), 404

    if current_user not in courseclass.students:
        return jsonify({"error": "Student is not in this course class"}), 400

    courseclass.students.remove(current_user)
    db.session.commit()

    return jsonify({"message": "Student left the course class successfully"}), 200





#查询单个课程班的所有学生信息
@courseclass_bp.route('/courseclasses/<int:courseclass_id>/students', methods=['GET'])
def get_students_by_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # 检查当前用户是否为该课程班的老师或学生
        if not is_teacher_of_courseclass(courseclass_id) and current_user not in Courseclass.query.get(courseclass_id).students:
            return jsonify({'error': 'You are not authorized to access students of this course class'}), 403

        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404

        students = courseclass.students

        result = [
            {
                'id': student.id,
                'username': student.username,
            }
            for student in students
        ]
        return jsonify({
            'total': len(result),
            'students': result
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#根据关键字搜索相关课程班
@courseclass_bp.route('/search_courseclasses', methods=['GET'])
def search_courseclasses():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 获取查询参数
        query = request.args.get('query', type=str)
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400

        # 获取当前登录用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # 根据用户角色进行不同的查询
        if current_user.role == 'teacher':
            # 查询当前老师的所有课程班
            courseclasses = Courseclass.query.join(teacher_class).filter(
                teacher_class.c.teacher_id == current_user.id,
                Courseclass.name.ilike(f'%{query}%')
            ).all()
        elif current_user.role == 'student':
            # 查询当前学生所属的所有课程班
            courseclasses = current_user.student_courseclasses.filter(
                Courseclass.name.ilike(f'%{query}%')
            ).all()
        else:
            return jsonify({'error': 'Invalid user role'}), 403

        result = [
            {
                'id': courseclass.id,
                'name': courseclass.name,
                'description': courseclass.description,
                'created_at': courseclass.created_at
            }
            for courseclass in courseclasses
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


@courseclass_bp.route('/courseclass')
def courseclasspage():
    return render_template('courseclass.html')