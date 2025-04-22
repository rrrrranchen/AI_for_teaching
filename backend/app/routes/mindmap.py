from collections import defaultdict
from datetime import datetime
from venv import logger
from flask import Blueprint, json, render_template, request, jsonify, session
from sqlalchemy import and_, desc, func
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.question import Question
from app.models.course import Course
from app.models.user import User
from app.models.courseclass import Courseclass
from app.services.lesson_plan import generate_ai_analysis, generate_post_class_questions, generate_pre_class_questions
from app.models.studentanswer import StudentAnswer
from app.models.teaching_design import TeachingDesign
from app.models.teachingdesignversion import TeachingDesignVersion
from app.models.MindMapNode import MindMapNode


mindmap_bp=Blueprint('mindmap',__name__)


def is_logged_in():
    return 'user_id' in session
# 获取当前登录的用户
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None




# 查询单个知识点的所有题目相关信息
@mindmap_bp.route('/knowledge/<int:knowledge_point_id>/questions', methods=['GET'])
def get_questions_by_knowledge_point(knowledge_point_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        knowledge_point = MindMapNode.query.get(knowledge_point_id)
        if not knowledge_point:
            return jsonify({'error': 'Knowledge point not found'}), 404

        design = TeachingDesign.query.get(knowledge_point.teachingdesignid)
        if not design:
            return jsonify({'error': 'Teaching design not found'}), 404

        course = Course.query.get(design.course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        course_class = Courseclass.query.filter(Courseclass.courses.contains(course)).first()
        if not course_class:
            return jsonify({'error': 'Course class not found'}), 404

        if current_user not in course_class.teachers :
            return jsonify({'error': 'Permission denied'}), 403

        def collect_leaf_questions(node):
            leaf_questions = {}
            if node.is_leaf:
                node_questions = Question.query.filter_by(knowledge_point_id=node.id).all()
                if node_questions:
                    leaf_questions[node.id] = {
                        'knowledge_point_name': node.node_name,
                        'knowledge_point_content': node.node_content,
                        'questions': []
                    }
                    for q in node_questions:
                        question_data = {
                            'id': q.id,
                            'course_id': q.course_id,
                            'type': q.type,
                            'content': q.content,
                            'correct_answer': q.correct_answer,
                            'difficulty': q.difficulty,
                            'timing': q.timing,
                            'is_public': q.is_public
                        }
                        # 添加统计信息（如果超过截止时间）
                        current_time = datetime.utcnow()
                        if course.post_class_deadline and current_time > course.post_class_deadline:
                            class_id = course_class.id
                            answers = StudentAnswer.query.filter_by(
                                question_id=q.id, 
                                class_id=class_id
                            ).all()
                            statistics = {}
                            
                            if q.type == 'choice':
                                option_counts = defaultdict(int)
                                total = len(answers)
                                correct_option = q.correct_answer.strip().upper()
                                for ans in answers:
                                    option = ans.answer.strip().upper()
                                    option_counts[option] += 1
                                options_stat = []
                                for opt, cnt in option_counts.items():
                                    percentage = (cnt / total * 100) if total > 0 else 0
                                    options_stat.append({
                                        'option': opt,
                                        'count': cnt,
                                        'percentage': round(percentage, 2),
                                        'is_correct': opt == correct_option
                                    })
                                statistics['options'] = options_stat
                                
                                # 计算选择题平均正确率
                                correct_count = option_counts.get(correct_option, 0)
                                avg_correct = (correct_count / total * 100) if total > 0 else 0
                                statistics['average_correct_percentage'] = round(avg_correct, 2)
                            
                            elif q.type == 'fill':
                                correct_count = 0
                                error_counts = defaultdict(int)
                                correct_answer = q.correct_answer.strip().lower()
                                for ans in answers:
                                    ans_text = ans.answer.strip().lower()
                                    if ans_text == correct_answer:
                                        correct_count += 1
                                    else:
                                        error_counts[ans_text] += 1
                                total = len(answers)
                                sorted_errors = sorted(error_counts.items(), key=lambda x: (-x[1], x[0]))
                                top_errors = [{'answer': k, 'count': v, 'percentage': round((v / total * 100), 2)} 
                                            for k, v in sorted_errors[:3]]
                                other_cnt = sum(v for k, v in sorted_errors[3:])
                                statistics.update({
                                    'correct': {
                                        'count': correct_count,
                                        'percentage': round((correct_count / total * 100), 2) if total > 0 else 0
                                    },
                                    'top_errors': top_errors,
                                    'other_errors': {
                                        'count': other_cnt,
                                        'percentage': round((other_cnt / total * 100), 2) if total > 0 else 0
                                    }
                                })
                                
                                # 计算填空题平均正确率
                                avg_correct = (correct_count / total * 100) if total > 0 else 0
                                statistics['average_correct_percentage'] = round(avg_correct, 2)
                            
                            elif q.type == 'short_answer':
                                ranges = {'0-25%': 0, '25-50%': 0, '50-75%': 0, '75-100%': 0}
                                total = len(answers)
                                sum_percentages = 0  # 新增用于存储总分值
                                
                                for ans in answers:
                                    perc = ans.correct_percentage
                                    sum_percentages += perc  # 累加每个答案的正确率
                                    if perc <= 25:
                                        ranges['0-25%'] += 1
                                    elif perc <= 50:
                                        ranges['25-50%'] += 1
                                    elif perc <= 75:
                                        ranges['50-75%'] += 1
                                    else:
                                        ranges['75-100%'] += 1
                                        
                                score_ranges = [{
                                    'range': k,
                                    'count': v,
                                    'percentage': round((v / total * 100), 2) if total > 0 else 0
                                } for k, v in ranges.items()]
                                statistics['score_ranges'] = score_ranges
                                
                                # 计算简答题平均正确率
                                avg_correct = (sum_percentages / total) if total > 0 else 0
                                statistics['average_correct_percentage'] = round(avg_correct, 2)
                            
                            question_data['statistics'] = statistics
                        
                        leaf_questions[node.id]['questions'].append(question_data)
            else:
                for child in node.children:
                    child_questions = collect_leaf_questions(child)
                    for k in child_questions:
                        leaf_questions[k] = child_questions[k]
            return leaf_questions

        leaf_questions_dict = collect_leaf_questions(knowledge_point)
        filtered_leaf_questions = []

        for leaf_id in leaf_questions_dict:
            leaf_info = leaf_questions_dict[leaf_id]
            filtered_questions = []
            for question in leaf_info['questions']:
                # 权限过滤
                if (current_user.role == 'student' and question['is_public']) or current_user.role != 'student':
                    filtered_questions.append(question)
            if filtered_questions:
                filtered_leaf_questions.append({
                    'knowledge_point_id': leaf_id,
                    'knowledge_point_name': leaf_info['knowledge_point_name'],
                    'knowledge_point_content': leaf_info['knowledge_point_content'],
                    'questions': filtered_questions
                })

        return jsonify({'leaf_questions': filtered_leaf_questions}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

#为单个知识点生成分析报告，会根据其叶子节点所有学生答题记录生成
@mindmap_bp.route('/knowledge/<int:knowledge_point_id>/ai_analysis', methods=['POST'])
def get_ai_analysis_by_knowledge_point(knowledge_point_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 获取当前登录用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # 查询知识点是否存在
        knowledge_point = MindMapNode.query.get(knowledge_point_id)
        if not knowledge_point:
            return jsonify({'error': 'Knowledge point not found'}), 404

        # 获取知识点所属的教学设计
        design = TeachingDesign.query.get(knowledge_point.teachingdesignid)
        if not design:
            return jsonify({'error': 'Teaching design not found'}), 404

        # 获取教学设计所属的课程
        course = Course.query.get(design.course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        # 获取课程所属的课程班
        course_class = Courseclass.query.filter(Courseclass.courses.contains(course)).first()
        if not course_class:
            return jsonify({'error': 'Course class not found'}), 404

        # 检查当前用户是否是课程班的老师
        if current_user not in course_class.teachers:
            return jsonify({'error': 'You do not have permission to access AI analysis for this knowledge point'}), 403

        # 递归查询知识点所有叶子节点
        leaf_nodes = []
        def collect_leaf_nodes(node):
            if node.is_leaf:
                leaf_nodes.append(node)
            else:
                for child in node.children:
                    collect_leaf_nodes(child)

        collect_leaf_nodes(knowledge_point)

        # 获取所有叶子节点下所有题目的学生作答情况
        student_answers_json = []
        for leaf in leaf_nodes:
            # 获取该叶子节点下所有题目
            questions = Question.query.filter_by(knowledge_point_id=leaf.id).all()
            for question in questions:
                # 获取题目下所有学生作答情况
                answers = StudentAnswer.query.filter_by(question_id=question.id).all()
                for answer in answers:
                    student_answers_json.append({
                        'question_id': question.id,
                        'question_content': question.content,
                        'student_id': answer.student_id,
                        'answer': answer.answer,
                        'correct_percentage': answer.correct_percentage
                    })

        # 调用 AI 生成简短分析报告
        analysis_report = generate_ai_analysis(knowledge_point.node_name, student_answers_json)

        # 将报告存储到 MindMapNode 表中
        knowledge_point.ai_analysis = json.dumps(analysis_report, ensure_ascii=False)
        db.session.commit()

        return jsonify({
            'knowledge_point_id': knowledge_point_id,
            'knowledge_point_name': knowledge_point.node_name,
            'analysis_report': analysis_report,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating AI analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500


#获取单个知识点的分析报告
@mindmap_bp.route('/knowledge/<int:knowledge_point_id>/ai_analysis', methods=['GET'])
def get_ai_analysis(knowledge_point_id):
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 获取当前登录用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # 查询知识点是否存在
        knowledge_point = MindMapNode.query.get(knowledge_point_id)
        if not knowledge_point:
            return jsonify({'error': 'Knowledge point not found'}), 404

        # 获取知识点所属的教学设计
        design = TeachingDesign.query.get(knowledge_point.teachingdesignid)
        if not design:
            return jsonify({'error': 'Teaching design not found'}), 404

        # 获取教学设计所属的课程
        course = Course.query.get(design.course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        # 获取课程所属的课程班
        course_class = Courseclass.query.filter(Courseclass.courses.contains(course)).first()
        if not course_class:
            return jsonify({'error': 'Course class not found'}), 404

        # 检查当前用户是否是课程班的老师
        if current_user not in course_class.teachers:
            return jsonify({'error': 'You do not have permission to access AI analysis for this knowledge point'}), 403

        # 获取 AI 分析报告
        ai_analysis = knowledge_point.ai_analysis
        if not ai_analysis:
            return jsonify({'error': 'No AI analysis available for this knowledge point'}), 404

        # 解析 AI 分析报告（假设存储的是 JSON 字符串）
        try:
            analysis_report = json.loads(ai_analysis)
        except json.JSONDecodeError:
            analysis_report = ai_analysis

        return jsonify({
            'knowledge_point_id': knowledge_point_id,
            'knowledge_point_name': knowledge_point.node_name,
            'analysis_report': analysis_report,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@mindmap_bp.route('/knowledge/<int:knowledge_point_id>/update', methods=['PUT'])
def update_knowledge_point(knowledge_point_id):
    """
    修改单个知识点信息，并更新教学设计的思维导图
    """
    if not is_logged_in():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        # 获取当前登录用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # 查询知识点是否存在
        knowledge_point = MindMapNode.query.get(knowledge_point_id)
        if not knowledge_point:
            return jsonify({'error': 'Knowledge point not found'}), 404

        # 获取知识点所属的教学设计
        design = TeachingDesign.query.get(knowledge_point.teachingdesignid)
        if not design:
            return jsonify({'error': 'Teaching design not found'}), 404

        # 获取教学设计所属的课程
        course = Course.query.get(design.course_id)
        if not course:
            return jsonify({'error': 'Course not found'}), 404

        # 获取课程所属的课程班
        course_class = Courseclass.query.filter(Courseclass.courses.contains(course)).first()
        if not course_class:
            return jsonify({'error': 'Course class not found'}), 404

        # 检查当前用户是否是课程班的老师
        if current_user not in course_class.teachers:
            return jsonify({'error': 'You do not have permission to update this knowledge point'}), 403

        # 获取请求中的 JSON 数据
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # 提取知识点信息
        new_node_name = data.get('node_name')
        new_node_content = data.get('node_content', '')  # 允许为空
        new_parent_node_id = data.get('parent_node_id')  # 可选，用于更改父节点

        # 如果提供了新的节点名称，更新节点名称
        if new_node_name is not None:
            knowledge_point.node_name = new_node_name

        # 如果提供了新的节点内容，更新节点内容
        if new_node_content is not None:
            knowledge_point.node_content = new_node_content

        # 如果提供了新的父节点 ID，更新父节点关系
        if new_parent_node_id is not None:
            # 验证新的父节点是否存在
            new_parent_node = MindMapNode.query.get(new_parent_node_id)
            if not new_parent_node:
                return jsonify({'error': 'New parent node not found'}), 404

            # 更新当前节点的父节点 ID
            knowledge_point.parent_node_id = new_parent_node_id

            # 如果新父节点 previously was a leaf node, update it to non-leaf
            if new_parent_node.is_leaf:
                new_parent_node.is_leaf = False
                db.session.add(new_parent_node)

        # 更新当前节点的 is_leaf 状态（如果适用）
        if knowledge_point.children:
            knowledge_point.is_leaf = False
        else:
            knowledge_point.is_leaf = True

        # 提交更改
        db.session.commit()

        # 更新教学设计的 mindmap 字段
        update_teaching_design_mindmap(design.id)

        return jsonify({
            'message': 'Knowledge point updated successfully',
            'knowledge_point_id': knowledge_point.id,
            'node_name': knowledge_point.node_name,
            'node_content': knowledge_point.node_content,
            'parent_node_id': knowledge_point.parent_node_id,
            'is_leaf': knowledge_point.is_leaf
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def update_teaching_design_mindmap(teaching_design_id):
    """
    更新教学设计的思维导图
    """
    try:
        # 查询教学设计
        design = TeachingDesign.query.get(teaching_design_id)
        if not design:
            return

        # 查询该教学设计的所有知识点
        top_level_nodes = MindMapNode.query.filter_by(
            teachingdesignid=teaching_design_id, 
            parent_node_id=None
        ).all()

        # 递归构建思维导图
        def build_mind_map(node):
            node_data = {
                "data": {  # 将节点信息包裹在 data 字段中
                   "id": node.id,
                   "text": node.node_name,
                   "note": node.node_content
                },
            "children": []
            }
            for child in node.children:
                node_data["children"].append(build_mind_map(child))
            return node_data

        # 构建完整的思维导图
        mind_map = []
        for root_node in top_level_nodes:
            mind_map.append(build_mind_map(root_node))

        # 将思维导图存储到 TeachingDesign 的 mindmap 字段
        design.mindmap = json.dumps(mind_map, ensure_ascii=False)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating teaching design mindmap: {str(e)}")


