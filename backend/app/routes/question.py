from venv import logger
from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.question import Question
from app.models.course import Course
from app.services.demo import mock_ai_interface
from app.models.user import User
from app.models.courseclass import Courseclass
question_bp=Blueprint('question',__name__)

def is_logged_in():
    return 'user_id' in session
# 获取当前登录的用户
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

#生成课前预习题目
@question_bp.route('/createprequestion/<int:course_id>', methods=['POST'])
def teachingdesign_create(course_id):
    # 检查用户是否登录
    if not is_logged_in():
        logger.warning("Unauthorized access attempt")
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            logger.error("Current user not found")
            return jsonify({'error': 'User not found'}), 404

        # 获取请求数据
        data = request.json
        if not data:
            logger.error("No data provided in request")
            return jsonify({'error': 'No data provided'}), 400

        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            logger.error(f"Course with ID {course_id} not found")
            return jsonify({'error': 'Course not found'}), 404

        # 获取课程所属的课程班
        course_class = Courseclass.query.filter(Courseclass.courses.contains(course)).first()
        if not course_class:
            logger.error(f"Course class for course ID {course_id} not found")
            return jsonify({'error': 'Course class not found'}), 404

        # 检查当前用户是否是课程班的老师
        if current_user not in course_class.teachers:
            logger.warning(f"User {current_user.id} does not have permission to create questions for course ID {course_id}")
            return jsonify({'error': 'You do not have permission to create questions for this course'}), 403

        # 获取课程描述
        course_description = course.description if course.description else ""

        # 调用模拟 AI 接口获取题目集合
        ai_questions = mock_ai_interface(data.get('content', ''), num_questions=5)  # 默认生成 5 个题目
        if not ai_questions:
            logger.error("No questions generated by AI")
            return jsonify({'error': 'Failed to generate questions'}), 500

        # 批量创建题目
        created_question_ids = []
        for ai_question in ai_questions:
            # 将课程描述整合到问题内容中
            content = f"{course_description}\n\n{ai_question['content']}" if course_description else ai_question['content']

            # 创建新的问题记录
            new_question = Question(
                course_id=course_id,
                type=ai_question['type'],
                content=content,
                correct_answer=ai_question['correct_answer'],
                difficulty=ai_question['difficulty'],
                timing='pre_class'
            )
            db.session.add(new_question)
            db.session.flush()  # 确保生成 ID
            created_question_ids.append(new_question.id)

        # 提交事务
        db.session.commit()
        logger.info(f"Successfully created {len(created_question_ids)} questions for course ID {course_id}")

        # 返回成功响应
        return jsonify({
            'message': 'Questions created successfully',
            'question_ids': created_question_ids
        }), 201

    except Exception as e:
        # 捕获异常并回滚事务
        db.session.rollback()
        logger.error(f"Error creating questions: {str(e)}")
        return jsonify({'error': str(e)}), 500

#删除单个题目
@question_bp.route('/deletequestion/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 获取当前登录用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # 查询要删除的题目
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404

        # 获取题目所属的课程
        course = Course.query.get(question.course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        # 获取课程所属的课程班
        course_class = Courseclass.query.filter(Courseclass.courses.contains(course)).first()
        if not course_class:
            return jsonify({'error': 'Course class not found'}), 404

        # 检查当前用户是否是课程班的老师
        if current_user not in course_class.teachers:
            return jsonify({'error': 'You do not have permission to delete this question'}), 403

        # 删除题目记录
        db.session.delete(question)
        db.session.commit()

        return jsonify({
            'message': 'Question deleted successfully',
            'question_id': question_id
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
# 查询单个课程的所有预习题目
@question_bp.route('/prequestions/<int:course_id>', methods=['GET'])
def get_questions_by_course(course_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 获取当前登录用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        # 获取课程所属的课程班
        course_class = Courseclass.query.filter(Courseclass.courses.contains(course)).first()
        if not course_class:
            return jsonify({'error': 'Course class not found'}), 404

        # 检查当前用户是否是课程班的老师或学生
        if current_user not in course_class.teachers and current_user not in course_class.students:
            return jsonify({'error': 'You do not have permission to access questions for this course'}), 403

        # 获取该课程的所有预习题目
        questions = Question.query.filter_by(course_id=course_id, timing='pre_class').all()

        # 返回题目列表
        return jsonify([{
            'id': question.id,
            'course_id': question.course_id,
            'type': question.type,
            'content': question.content,
            'correct_answer': question.correct_answer,
            'difficulty': question.difficulty,
            'timing': question.timing
        } for question in questions]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 查询单个题目
@question_bp.route('/question/<int:question_id>', methods=['GET'])
def get_question(question_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 获取当前登录用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # 查询题目
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404

        # 获取题目所属的课程
        course = Course.query.get(question.course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        # 获取课程所属的课程班
        course_class = Courseclass.query.filter(Courseclass.courses.contains(course)).first()
        if not course_class:
            return jsonify({'error': 'Course class not found'}), 404

        # 检查当前用户是否是课程班的老师
        if current_user not in course_class.teachers:
            return jsonify({'error': 'You do not have permission to view this question'}), 403

        # 返回题目详情
        return jsonify({
            'id': question.id,
            'course_id': question.course_id,
            'type': question.type,
            'content': question.content,
            'correct_answer': question.correct_answer,
            'difficulty': question.difficulty,
            'timing': question.timing
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# 修改单个题目
@question_bp.route('/question/<int:question_id>', methods=['PUT'])
def update_question(question_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 获取当前登录用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # 查询要修改的题目
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404

        # 获取题目所属的课程
        course = Course.query.get(question.course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        # 获取课程所属的课程班
        course_class = Courseclass.query.filter(Courseclass.courses.contains(course)).first()
        if not course_class:
            return jsonify({'error': 'Course class not found'}), 404

        # 检查当前用户是否是课程班的老师
        if current_user not in course_class.teachers:
            return jsonify({'error': 'You do not have permission to update this question'}), 403

        # 获取请求中的 JSON 数据
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # 更新题目信息
        question.type = data.get('type', question.type)
        question.content = data.get('content', question.content)
        question.correct_answer = data.get('correct_answer', question.correct_answer)
        question.difficulty = data.get('difficulty', question.difficulty)
        question.timing = data.get('timing', question.timing)

        # 提交更改
        db.session.commit()

        return jsonify({
            'message': 'Question updated successfully',
            'question_id': question.id
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@question_bp.route('/question-page')
def questiontest():
    return render_template('question.html')