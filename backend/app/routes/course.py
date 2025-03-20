from flask import Blueprint, render_template, request, jsonify, session
from app.utils.database import db
from app.models.course import Course
from app.models.courseclass import Courseclass

course_bp = Blueprint('course', __name__)

# 检查用户是否登录
def is_logged_in():
    return 'user_id' in session

# 查询所有课程
@course_bp.route('/courses', methods=['GET'])
def get_courses():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        
        courses = Course.query.all()
        
        result = [
            {
                'id': course.id,
                'name': course.name,
                'description': course.description,
                'created_at': course.created_at,
                'courseclasses': [{'id': cc.id, 'name': cc.name} for cc in course.courseclasses]
            }
            for course in courses
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 根据 ID 查询单个课程
@course_bp.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
       
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        result = {
            'id': course.id,
            'name': course.name,
            'description': course.description,
            'created_at': course.created_at,
            'courseclasses': [{'id': cc.id, 'name': cc.name} for cc in course.courseclasses]
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
        courseclass_ids = data.get('courseclass_ids', [])  # 获取课程班 ID 列表
        
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        new_course = Course(name=name, description=description)
        
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
        
        data = request.json
        name = data.get('name')
        description = data.get('description')
        courseclass_ids = data.get('courseclass_ids', [])  # 获取课程班 ID 列表
        
        if name:
            course.name = name
        if description:
            course.description = description
        
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

# 为课程添加课程班
@course_bp.route('/courses/<int:course_id>/add_courseclass', methods=['POST'])
def add_courseclass_to_course(course_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
       
        data = request.json
        courseclass_id = data.get('courseclass_id')
        if not courseclass_id:
            return jsonify({'error': 'CourseClass ID is required'}), 400
        
        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404
        
        course.courseclasses.append(courseclass)
        db.session.commit()
        return jsonify({'message': 'CourseClass added to Course successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 从课程中删除课程班
@course_bp.route('/courses/<int:course_id>/remove_courseclass', methods=['POST'])
def remove_courseclass_from_course(course_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        data = request.json
        courseclass_id = data.get('courseclass_id')
        if not courseclass_id:
            return jsonify({'error': 'CourseClass ID is required'}), 400
        
        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404
        
        if courseclass in course.courseclasses:
            course.courseclasses.remove(courseclass)
            db.session.commit()
        else:
            return jsonify({'error': 'CourseClass is not associated with this Course'}), 400
        return jsonify({'message': 'CourseClass removed from Course successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500