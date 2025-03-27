from datetime import datetime
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
from app.models import course
from app.services.autogra_service import ChineseGrader
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

    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少数据'}), 400

    question_id = data.get('question_id')
    class_id = data.get('class_id')
    answer = data.get('answer')

    if not all([question_id, class_id, answer]):
        return jsonify({'error': '缺少必要参数'}), 400

    # 检查是否为该班学生
    if not is_student_of_courseclass(class_id):
        return jsonify({'error': 'You are not authorized to access this course'}), 403

    try:
        # 获取题目信息
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404

        # 检查是否已经存在该学生的答题记录
        existing_answer = StudentAnswer.query.filter_by(
            student_id=current_user.id,
            question_id=question_id
        ).first()

        # 根据题目类型评分
        if question.type in ['choice', 'fill']:
            # 选择题和填空题：直接对比答案
            correct_percentage = 100 if answer.strip() == question.correct_answer.strip() else 0
        elif question.type == 'short_answer':
            # 简答题：使用 ChineseGrader 评估
            grader = ChineseGrader()
            grading_result = grader.grade(question.correct_answer, answer, max_score=10)
            correct_percentage = grading_result['score'] * 10  # 转换为百分比
        else:
            return jsonify({'error': 'Unsupported question type'}), 400

        # 如果已经存在答题记录，更新记录
        if existing_answer:
            existing_answer.answer = answer
            existing_answer.correct_percentage = correct_percentage
            existing_answer.answered_at = datetime.utcnow()
            db.session.commit()
            return jsonify({
                'message': '答题记录更新成功',
                'answer_id': existing_answer.id,
                'correct_percentage': correct_percentage
            }), 200
        else:
            # 添加新的答题记录
            new_answer = StudentAnswer(
                student_id=current_user.id,
                question_id=question_id,
                class_id=class_id,
                answer=answer,
                correct_percentage=correct_percentage
            )
            db.session.add(new_answer)
            db.session.commit()
            return jsonify({
                'message': '答题记录添加成功',
                'answer_id': new_answer.id,
            }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'添加失败：{str(e)}'}), 500

#教师更新作答成绩
@studentanswer_bp.route('/update_score', methods=['POST'])
def update_score():
    # 身份验证
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401
    
    current_user = get_current_user()
    if not current_user or current_user.role != 'teacher':
        return jsonify({'error': '无权限操作'}), 403

    # 数据验证
    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少数据'}), 400

    answer_id = data.get('answer_id')
    class_id = data.get('class_id')
    new_score = data.get('new_score')

    if None in [answer_id, class_id, new_score]:
        return jsonify({'error': '缺少必要参数'}), 400

    try:
        # 权限验证
        if not is_teacher_of_courseclass(class_id):
            return jsonify({'error': '您不是该课程班的老师'}), 403

        # 获取答题记录
        student_answer = StudentAnswer.query.filter_by(
            id=answer_id,
            class_id=class_id
        ).first()

        if not student_answer:
            return jsonify({'error': '答题记录不存在或不属于该班级'}), 404

        # 分数范围验证
        if not 0 <= new_score <= 100:
            return jsonify({'error': '分数必须在0-100之间'}), 400

        # 更新记录
        student_answer.correct_percentage = new_score
        student_answer.modified_by = current_user.id
        student_answer.modified_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': '分数修改成功',
            'data': {
                'answer_id': student_answer.id,
                'new_score': new_score,
                'modified_at': student_answer.modified_at.isoformat()
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500
    
#查询单个题目
@studentanswer_bp.route('/<int:answer_id>', methods=['GET'])
def get_answer(answer_id):
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    answer = StudentAnswer.query.get(answer_id)
    if not answer:
        return jsonify({'error': '答题记录不存在'}), 404

    # 权限检查：学生本人或班级老师
    current_user = get_current_user()
    if not (current_user.id == answer.student_id or 
            (current_user.role == 'teacher' and 
             is_teacher_of_courseclass(answer.class_id))):
        return jsonify({'error': '无权查看此记录'}), 403

    response_data = {
        'id': answer.id,
        'student_id': answer.student_id,
        'question_id': answer.question_id,
        'class_id': answer.class_id,
        'answer': answer.answer,
        'score': answer.correct_percentage,
        'answered_at': answer.answered_at.isoformat(),
        'is_modified': answer.modified_at is not None
    }

    if response_data['is_modified']:
        # 直接查询用户表获取修改者信息
        modifier = User.query.get(answer.modified_by)
        response_data.update({
            'modified_at': answer.modified_at.isoformat(),
            'modified_by': modifier.username if modifier else None
        })

    return jsonify(response_data), 200


#教师查询单个课程的所有题目学生作答情况
@studentanswer_bp.route('/course/<int:course_id>/answers', methods=['GET'])
def get_course_answers(course_id):
    # 验证登录状态
    if not is_logged_in():
        return jsonify({'error': '未登录'}), 401

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': '用户不存在'}), 404

    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    if page < 1 or per_page < 1:
        return jsonify({'error': '无效的分页参数'}), 400

    try:
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': '课程不存在'}), 404

        # 获取课程关联的所有课程班ID
        class_ids = [c.id for c in course.courseclasses]

        # 构建基础查询
        query = db.session.query(
            StudentAnswer,
            Question,
            User.username.label('student_name')
        ).join(
            Question, StudentAnswer.question_id == Question.id
        ).join(
            User, StudentAnswer.student_id == User.id
        ).filter(
            StudentAnswer.class_id.in_(class_ids)
        )

        # 权限过滤
        if current_user.role == 'student':
            query = query.filter(StudentAnswer.student_id == current_user.id)
        elif current_user.role == 'teacher':
            # 验证是否是课程关联班级的老师
            if not any(is_teacher_of_courseclass(cid) for cid in class_ids):
                return jsonify({'error': '无权限访问该课程数据'}), 403
        else:
            return jsonify({'error': '无效的用户角色'}), 403

        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        answers = pagination.items

        # 构建响应数据
        result = []
        for answer, question, student_name in answers:
            answer_data = {
                'answer_id': answer.id,
                'student_id': answer.student_id,
                'student_name': student_name,
                'question_id': question.id,
                'question_content': question.content,
                'answer_content': answer.answer,
                'score': answer.correct_percentage,
                'answered_at': answer.answered_at.isoformat(),
                'is_modified': answer.modified_at is not None
            }
            if answer_data['is_modified']:
                modifier = User.query.get(answer.modified_by)
                answer_data.update({
                    'modified_at': answer.modified_at.isoformat(),
                    'modified_by': modifier.username if modifier else None
                })
            result.append(answer_data)

        return jsonify({
            'items': result,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200

    except Exception as e:
        logger.error(f"查询失败: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500
    
    