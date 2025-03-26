from venv import logger
from flask import Blueprint, render_template, request, jsonify, session
from sqlalchemy import func, select
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.question import Question
from app.models.course import Course
from app.services.demo import mock_ai_interface
from app.models.user import User
from app.models.courseclass import Courseclass
from app.models.relationship import teacher_class
from app.models.studentanswer import StudentAnswer
from app.models.relationship import student_class
from backend.app.models import course
studentanswer_bp=Blueprint('studentanswer',__name__)

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

#验证是否为指定课程班的学生
def is_student_of_courseclass(courseclass_id):
    current_user = get_current_user()
    if not current_user or current_user.role != 'student':
        return False

    # 查询 student_class 表，检查当前用户是否为课程班的学生
    association = db.session.scalar(
        select(func.count()).where(
            student_class.c.student_id == current_user.id,
            student_class.c.class_id == courseclass_id
        )
    )
    return association > 0

#学生作答
@studentanswer_bp.route('/add_answer', methods=['POST'])
def add_answer():
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404
    if not any(is_student_of_courseclass(cc.id) for cc in course.courseclasses):
            return jsonify({'error': 'You are not authorized to access this course'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少数据'}), 400

    student_id = 'user_id' in session
    question_id = data.get('question_id')
    class_id = data.get('class_id')
    answer = data.get('answer')
    correct_percentage = data.get('correct_percentage')

    if not all([student_id, question_id, class_id, answer, correct_percentage]):
        return jsonify({'error': '缺少必要参数'}), 400

    try:
        new_answer = StudentAnswer(
            student_id=student_id,
            question_id=question_id,
            class_id=class_id,
            answer=answer,
            correct_percentage=correct_percentage
        )
        db.session.add(new_answer)
        db.session.commit()
        return jsonify({'message': '答题记录添加成功', 'answer_id': new_answer.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'添加失败：{str(e)}'}), 500
