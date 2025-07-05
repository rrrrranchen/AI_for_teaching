from datetime import datetime
import random
import string
from flask import Blueprint, current_app, g, render_template, request, jsonify, session
from pymysql import IntegrityError
from sqlalchemy import func, select
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.courseclass import Courseclass
from app.models.course import Course
from app.models.user import User
from app.models.relationship import teacher_class,student_class,course_courseclass
from app.models.question import Question
from app.utils.file_upload import upload_file_courseclass
from app.services.rank import generate_class_recommend_ranking, generate_public_courseclass_ranking
from app.models import CourseClassApplication
from app.services.log_service import LogService
courseclass_bp = Blueprint('courseclass', __name__)

def is_logged_in():
    return 'user_id' in session
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

@courseclass_bp.before_request
def before_request():
    # 检查用户是否已登录
    if request.method == 'OPTIONS':
        return
    if is_logged_in():
        # 获取当前用户并存储到 g 对象中
        g.current_user = get_current_user()
    else:
        # 如果用户未登录，返回未授权错误
        return jsonify({'error': 'Unauthorized'}), 401

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
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        if current_user.role == 'teacher':
            courseclasses = Courseclass.query.options(
                db.joinedload(Courseclass.teachers),
                db.joinedload(Courseclass.courses)
            ).join(
                teacher_class,
                Courseclass.id == teacher_class.c.class_id  # 使用 class_id
            ).filter(
                teacher_class.c.teacher_id == current_user.id
            ).all()
        elif current_user.role == 'student':
            courseclasses = Courseclass.query.options(
                db.joinedload(Courseclass.students),
                db.joinedload(Courseclass.courses)
            ).join(
                student_class,
                Courseclass.id == student_class.c.class_id  # 使用 class_id
            ).filter(
                student_class.c.student_id == current_user.id
            ).all()
        else:
            return jsonify({'error': 'Invalid user role'}), 403

        result = [
            {
                'id': courseclass.id,
                'name': courseclass.name,
                'description': courseclass.description,
                'created_at': courseclass.created_at,
                'invite_code': courseclass.invite_code,
                'image_path' : courseclass.image_path,
                'course_count':len(courseclass.courses),
                'teachers': [
                    {'id': teacher.id, 'username': teacher.username,'avatar':teacher.avatar}
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
        if not courseclass.is_public and not is_teacher_of_courseclass(courseclass_id) and current_user not in courseclass.students:
            return jsonify({'error': 'You are not authorized to access this course class'}), 403

        result = {
            'id': courseclass.id,
            'name': courseclass.name,
            'description': courseclass.description,
            'created_at': courseclass.created_at,
            'invite_code': courseclass.invite_code,
            'image_path' : courseclass.image_path,
            'student_count': len(courseclass.students),
            'course_count': len(courseclass.courses),
            'teachers': [
                    {'id': teacher.id, 'username': teacher.username, 'avatar': teacher.avatar}
                    for teacher in courseclass.teachers
                ],
            'courses': [{'id': course.id, 'name': course.name} for course in courseclass.courses]
            
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

 #        获取请求数据
        data = request.form
        name = data.get('name')
        description = data.get('description')
        is_public_str = data.get('is_public', 'false')  # 获取是否公开字段，默认值为 'false'
        is_public = is_public_str.lower() == 'true'  # 将字符串转换为布尔值
        image_file = request.files.get('image')  # 获取上传的图片文件
        
        if not name:
            return jsonify({'error': 'Name is required'}), 400

        # 生成邀请码
        invite_code = generate_invite_code()

        # 创建新的课程班
        new_courseclass = Courseclass(
            name=name,
            description=description,
            invite_code=invite_code,
            is_public=is_public  # 设置是否公开字段
        )

        # 上传图片并保存路径
        if image_file:
            image_path = upload_file_courseclass(image_file)
            new_courseclass.image_path = image_path
        else:
            new_courseclass.image_path = 'static/uploads/courseclass/default.jpg'  # 使用默认图片路径

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
            'invite_code': new_courseclass.invite_code,
            'image_path': new_courseclass.image_path,  # 返回图片路径
            'is_public': new_courseclass.is_public  # 返回是否公开字段
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

# 为课程班创建课程
@courseclass_bp.route('/courseclasses/<int:courseclass_id>/create_course', methods=['POST'])
def create_course_for_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 检查当前用户是否为该课程班的老师
        if not is_teacher_of_courseclass(courseclass_id):
            return jsonify({'error': 'You are not authorized to create courses for this course class'}), 403

        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404

        # 获取请求数据
        data = request.json
        name = data.get('name')
        description = data.get('description')

        if not name:
            return jsonify({'error': 'Name is required'}), 400

        # 创建新的课程
        new_course = Course(name=name, description=description)
        db.session.add(new_course)
        db.session.flush()  # 获取 new_course.id

        # 将课程添加到课程班
        courseclass.courses.append(new_course)
        db.session.commit()

        return jsonify({
            'id': new_course.id,
            'name': new_course.name,
            'description': new_course.description,
            'created_at': new_course.created_at
        }), 201
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



@courseclass_bp.route('/courseclasses/<int:courseclass_id>/courses', methods=['GET'])
def get_courses_by_courseclass(courseclass_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        current_user=get_current_user()
        # 检查当前用户是否为该课程班的老师
        if not is_teacher_of_courseclass(courseclass_id) and current_user not in Courseclass.query.get(courseclass_id).students:
            return jsonify({'error': 'You are not authorized to access students of this course class'}), 403

        courseclass = Courseclass.query.get(courseclass_id)
        if not courseclass:
            return jsonify({'error': 'CourseClass not found'}), 404

        courses = courseclass.courses

        result = [
            {
                'id': course.id,
                'name': course.name,
                'description': course.description,
                'has_public_questions': Question.query.filter_by(course_id=course.id, is_public=True).count() > 0
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

#学生离开课程班
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
                'avatar':student.avatar
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
    
# 查询所有公开的课程班
@courseclass_bp.route('/public_courseclasses', methods=['GET'])
def get_public_courseclasses():
    try:
        # 获取搜索查询参数
        search_query = request.args.get('search', '', type=str)

        # 构建基础查询
        query = Courseclass.query.filter_by(is_public=True)

        # 添加搜索条件
        if search_query:
            query = query.filter(Courseclass.name.ilike(f'%{search_query}%'))

        # 获取所有符合条件的公开课程班
        public_courseclasses = query.order_by(Courseclass.created_at.desc()).all()

        # 构建返回结果
        result = [
            {
                'id': courseclass.id,
                'name': courseclass.name,
                'description': courseclass.description,
                'created_at': courseclass.created_at,
                'image_path': courseclass.image_path,
                'teacher_count': len(courseclass.teachers),
                'student_count': len(courseclass.students),
                'course_count': len(courseclass.courses),
                'teachers': [
                    {'id': teacher.id, 'username': teacher.username, 'avatar': teacher.avatar}
                    for teacher in courseclass.teachers
                ]
            }
            for courseclass in public_courseclasses
        ]

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#查询课程班级学生综合指数排行榜
@courseclass_bp.route('/query_student_rank/<int:courseclass_id>', methods=['GET'])
def query_student_rank(courseclass_id):
    """
    查询课程班级学生综合指数排行榜接口
    返回按综合评分排序的学生排行榜
    
    参数:
        courseclass_id: 课程班级ID
        
    返回:
        JSON格式的响应，包含:
        - code: 状态码(200表示成功)
        - message: 状态信息
        - data: 学生排行榜数据列表
    """
    try:
        # 调用生成排行榜的函数
        ranking_data = generate_class_recommend_ranking(courseclass_id)
        
        # 检查是否返回了错误响应
        if isinstance(ranking_data, tuple) and "error" in ranking_data[0]:
            return jsonify({
                "code": 404,
                "message": ranking_data[0]["error"],
                "data": None
            }), 404
        
        # 成功响应
        return jsonify({
            "code": 200,
            "message": "Success",
            "data": ranking_data
        })
    except Exception as e:
        # 捕获并处理意外错误
        current_app.logger.error(f"Error querying student rank: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Internal server error: {str(e)}",
            "data": None
        }), 500
    

@courseclass_bp.route('/query_courseclass_rank', methods=['GET'])
def query_courseclass_rank():

    try:
        ranking_data = generate_public_courseclass_ranking()
        
        if not ranking_data:
            return jsonify({
                "code": 404,
                "message": "No public course classes found",
                "data": None
            }), 404
            
        return jsonify({
            "code": 200,
            "message": "Success",
            "data": ranking_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating course class ranking: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"Internal server error: {str(e)}",
            "data": None
        }), 500
    
# 基于学生已加入的课程和热门程度推荐课程
@courseclass_bp.route('/courseclass/recommend_courseclasses', methods=['GET'])
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
@courseclass_bp.route('/courseclass/<int:courseclass_id>/apply', methods=['POST'])
def apply_to_courseclass(courseclass_id):
    try:
        if not is_logged_in():
            return jsonify({'error': 'Unauthorized'}), 401

        courseclass = Courseclass.query.get_or_404(courseclass_id)
        current_user = g.current_user

        if not courseclass.is_public:
            return jsonify({'error': '该课程班未公开，无法申请加入'}), 403

        # 检查用户是否是学生
        if current_user.role != 'student':
            return jsonify({'error': '只有学生可以申请加入课程班'}), 403

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
@courseclass_bp.route('/courseclass/<int:courseclass_id>/applications', methods=['GET'])
def get_courseclass_applications(courseclass_id):
    try:
        if not is_logged_in():
            return jsonify({'error': 'Unauthorized'}), 401

        courseclass = Courseclass.query.get_or_404(courseclass_id)
        current_user = g.current_user

        # 验证教师权限
        if current_user not in courseclass.teachers and current_user.role != 'teacher':
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

@courseclass_bp.route('/courseclass/applications/<int:application_id>/process', methods=['POST'])
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

@courseclass_bp.route('/courseclass/my_applications', methods=['GET'])
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
    

@courseclass_bp.after_request
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