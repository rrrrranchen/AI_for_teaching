from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.courseclass import Courseclass
from app.models.course import Course

courseclass_bp = Blueprint('courseclass', __name__)

# 检查用户是否登录
def is_logged_in():
    return 'user_id' in session

# 查询所有课程班
@courseclass_bp.route('/courseclasses', methods=['GET'])
def get_courseclasses():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
       
        courseclasses = Courseclass.query.all()
     
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

# 创建新的课程班
@courseclass_bp.route('/courseclasses', methods=['POST'])
def create_courseclass():
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
       
        data = request.json
        name = data.get('name')
        description = data.get('description')
    
        if not name:
            return jsonify({'error': 'Name is required'}), 400
    
        new_courseclass = Courseclass(name=name, description=description)
        db.session.add(new_courseclass)
        db.session.commit()
      
        return jsonify({
            'id': new_courseclass.id,
            'name': new_courseclass.name,
            'description': new_courseclass.description,
            'created_at': new_courseclass.created_at
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 更新课程班信息
@courseclass_bp.route('/courseclasses/<int:courseclass_id>', methods=['PUT'])
def update_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
       
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

# 删除课程班
@courseclass_bp.route('/courseclasses/<int:courseclass_id>', methods=['DELETE'])
def delete_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
       
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
@courseclass_bp.route('/courseclasses/<int:courseclass_id>/add_course', methods=['POST'])
def add_course_to_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        
        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404
        
        data = request.json
        course_id = data.get('course_id')
        if not course_id:
            return jsonify({'error': 'Course ID is required'}), 400
       
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
     
        courseclass.courses.append(course)
        db.session.commit()
        return jsonify({'message': 'Course added to CourseClass successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 从课程班中删除课程
@courseclass_bp.route('/courseclasses/<int:courseclass_id>/remove_course', methods=['POST'])
def remove_course_from_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
       
        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404
       
        data = request.json
        course_id = data.get('course_id')
        if not course_id:
            return jsonify({'error': 'Course ID is required'}), 400
        
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        if course in courseclass.courses:
            courseclass.courses.remove(course)
            db.session.commit()
        else:
            return jsonify({'error': 'Course is not associated with this CourseClass'}), 400
        return jsonify({'message': 'Course removed from CourseClass successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 根据课程班 ID 查找所有所属课程班的课程
@courseclass_bp.route('/courseclasses/<int:courseclass_id>/courses', methods=['GET'])
def get_courses_by_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        
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