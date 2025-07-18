import asyncio
from datetime import datetime
import os
import uuid
from venv import logger
from flask import Blueprint, app, current_app, g, json, make_response, redirect, render_template, request, jsonify, send_file, session
from jwt import InvalidKeyError
from pymysql import IntegrityError
from sqlalchemy import func, select
from app.utils.database import db
from app.models.user import User
from app.models.courseclass import Courseclass
from app.models.relationship import teacher_class
from app.models.course import Course
from app.models.teaching_design import TeachingDesign
from app.models.teachingdesignversion import TeachingDesignVersion
from app.models.question import Question
from app.services.lesson_plan import generate_knowledge_mind_map, generate_lesson_plans
from app.models.MindMapNode import MindMapNode
from app.models.studentanswer import StudentAnswer
from app.models.teachingDesignTime import TeachingDesignTime
from app.services.log_service import LogService

teaching_design_bp=Blueprint('teachingdesign',__name__)
def is_logged_in():
    return 'user_id' in session
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

@teaching_design_bp.before_request
def before_request():
    if request.method == 'OPTIONS':
        return
    # 检查用户是否已登录
    if is_logged_in():
        # 获取当前用户并存储到 g 对象中
        g.current_user = get_current_user()
        # 检查用户权限，只有管理员和教师可以查看
        if g.current_user and g.current_user.role != 'teacher' and g.current_user.role != 'admin':
            return jsonify({"error":'Forbidden'}), 403
    else:
        # 如果用户未登录，返回未授权错误
        return jsonify({'error': 'Unauthorized'}), 401


def calculate_node_color(knowledge_point_id):
    """ 定义一个函数来计算节点颜色 """
    # 获取该知识点及其所有子节点
    def get_all_descendant_nodes(node_id):
        nodes = []
        stack = [node_id]
        while stack:
            current_node_id = stack.pop()
            current_node = MindMapNode.query.get(current_node_id)
            if not current_node:
                continue
            nodes.append(current_node)
            
            for child in current_node.children:
                stack.append(child.id)
        return nodes

    # 获取知识点及其所有子节点
    all_nodes = get_all_descendant_nodes(knowledge_point_id)

    # 收集所有相关题目ID
    question_ids = []
    for node in all_nodes:
        questions = Question.query.filter_by(knowledge_point_id=node.id).all()
        question_ids.extend(q.id for q in questions)

    # 如果没有相关题目，返回白色
    if not question_ids:
        return '#ffffff'

    # 获取所有相关题目的学生作答情况
    answers = StudentAnswer.query.filter(StudentAnswer.question_id.in_(question_ids)).all()

    # 如果没有学生作答，返回基准色#ff7373
    if not answers:
        return '#ffffff'

    # 计算平均正确率（限制在0-100范围）
    total_correct = sum(answer.correct_percentage for answer in answers)
    avg_correct = max(0, min(total_correct / len(answers), 100))
    base_gb = 115  
    target_gb = 255  
    
    # 计算当前绿色/蓝色值
    gb_value = int(base_gb + (target_gb - base_gb) * (avg_correct / 100))
    gb_hex = f'{gb_value:02x}'
    
    return f'#ff{gb_hex}{gb_hex}'  # 格式：#ff[GB][GB]

def get_pre_class_questions_as_feedback(course_id):
    """
    提取指定课程的课前预习题目及学生答题情况，作为student_feedback参数
    :param course_id: 课程ID
    :return: 格式化后的学生反馈字符串，包含题目和答题情况
    """
    # 查询该课程的所有课前预习题目及相关学生答案（单次查询优化）
    pre_class_questions = (Question.query
                          .filter_by(course_id=course_id, timing='pre_class', is_public=True)
                          .options(db.joinedload(Question.answers))
                          .all())

    if not pre_class_questions:
        return "该课程暂无课前预习题目"

    feedback_lines = ["课前预习题目及学生答题情况汇总:"]
    all_answers = []
    question_stats = []

    for question in pre_class_questions:
        answers = question.answers
        all_answers.extend(answers)
        
        # 计算当前题目的统计
        total_answers = len(answers)
        correct_count = sum(1 for a in answers if a.correct_percentage >= 80)
        correct_rate = (correct_count / total_answers * 100) if total_answers > 0 else 0
        avg_correct = sum(a.correct_percentage for a in answers) / total_answers if total_answers > 0 else 0
        
        question_stats.append({
            'question': question,
            'total_answers': total_answers,
            'correct_rate': correct_rate,
            'avg_correct': avg_correct
        })

        # 添加题目信息到反馈
        feedback_lines.append(f"\n题目ID: {question.id}")
        feedback_lines.append(f"题型: {get_question_type_name(question.type)}")
        feedback_lines.append(f"内容: {question.content[:50]}...")
        feedback_lines.append(f"难度: {question.difficulty if question.difficulty else '未设置'}")

        if total_answers > 0:
            feedback_lines.append(f"答题情况: {correct_count}/{total_answers}人答对 (正确率: {correct_rate:.1f}%)")
            
            # 添加常见错误示例
            wrong_answers = [a.answer for a in answers if a.correct_percentage < 80]
            if wrong_answers:
                common_wrong = max(set(wrong_answers), key=wrong_answers.count)
                feedback_lines.append(f"常见错误答案示例: '{common_wrong[:50]}...'")  # 限制错误答案长度
        else:
            feedback_lines.append("暂无学生答题数据")

    # 添加总体统计
    if all_answers:
        total_questions = len(pre_class_questions)
        total_attempts = len(all_answers)
        overall_avg = sum(a.correct_percentage for a in all_answers) / total_attempts

        feedback_lines.append("\n总体统计:")
        feedback_lines.append(f"- 预习题目数量: {total_questions}题")
        feedback_lines.append(f"- 学生答题人次: {total_attempts}次")
        feedback_lines.append(f"- 平均正确率: {overall_avg:.1f}%")

        # 找出最难和最易的题目
        if len(question_stats) > 1:
            hardest = min(question_stats, key=lambda x: x['avg_correct'])
            easiest = max(question_stats, key=lambda x: x['avg_correct'])
            
            feedback_lines.append(f"- 最难题目: 题目ID {hardest['question'].id} (平均正确率: {hardest['avg_correct']:.1f}%)")
            feedback_lines.append(f"- 最易题目: 题目ID {easiest['question'].id} (平均正确率: {easiest['avg_correct']:.1f}%)")
    print(feedback_lines)
    return "\n".join(feedback_lines)

def get_question_type_name(type_enum):
    """辅助函数：获取题型名称"""
    return {
        'choice': '选择题',
        'fill': '填空题',
        'short_answer': '简答题'
    }.get(type_enum, '未知题型')

def is_teacher_of_course(course_id):
    """检查当前用户是否是课程的任课老师"""
    current_user = get_current_user()
    if not current_user or current_user.role != 'teacher':
        return False
    
    # 获取课程所属的课程班
    course = Course.query.get(course_id)
    if not course:
        return False
    
    course_class = Courseclass.query.filter(Courseclass.courses.contains(course)).first()
    if not course_class:
        return False
    
    # 检查用户是否是课程班的老师
    association = db.session.scalar(
        select(func.count()).where(
            teacher_class.c.teacher_id == current_user.id,
            teacher_class.c.class_id == course_class.id
        )
    )
    return association > 0


async def generate_teaching_plans_async(course_content, student_feedback,db_names,similarity_threshold,chunk_cnt):
    """异步生成单个教学方案"""
    await asyncio.sleep(1)  
    
    return generate_lesson_plans(course_content=course_content, student_feedback=student_feedback,db_names=db_names,similarity_threshold=similarity_threshold,chunk_cnt=chunk_cnt)

async def save_teaching_design_version_async(new_design, plan_content):
    """异步保存单个教学设计版本"""
    version = TeachingDesignVersion(
        design_id=new_design.id,
        version='1',  # 固定为版本1
        content=plan_content,
        recommendation_score=5,  # 默认推荐指数为5（最高）
        level='优秀',  # 默认等级为优秀
        author_id=new_design.creator_id
    )
    db.session.add(version)
    await asyncio.to_thread(db.session.commit)
    return version

async def set_current_version_async(new_design, versions):
    """异步设置当前版本"""
    best_version = max(versions, key=lambda v: v.recommendation_score)
    new_design.current_version_id = best_version.id
    await asyncio.to_thread(db.session.commit)




@teaching_design_bp.route('/createteachingdesign', methods=['POST'])
async def create_teaching_design():
    """异步创建教学设计（基于课程目标和内容）"""
    try:
        # 1. 身份验证和基础校验
        current_user = get_current_user()
        if not current_user or current_user.role != 'teacher':
            logger.warning(f"无操作权限尝试: 用户ID={getattr(current_user, 'id', 'None')}")
            return jsonify(code=403, message="无操作权限"), 403

        data = request.get_json()
        if not data or 'course_id' not in data:
            logger.warning("缺少必要参数: course_id")
            return jsonify(code=400, message="缺少必要参数"), 400

        # 2. 获取课程信息（包含课程目标和内容）
        course = Course.query.get(data['course_id'])
        if not course:
            logger.warning(f"课程不存在: course_id={data['course_id']}")
            return jsonify(code=404, message="课程不存在"), 404
            
        if not course.courseclasses:
            logger.warning(f"课程未关联课程班: course_id={data['course_id']}")
            return jsonify(code=400, message="课程未关联任何课程班"), 400
            
        courseclass = course.courseclasses[0]

        # 3. 检查课程目标和内容是否已设置
        if not course.objectives or not course.content:
            logger.warning(f"课程目标或内容未设置: course_id={data['course_id']}")
            return jsonify(code=400, message="请先设置课程目标和内容"), 400

        # 4. 获取知识库
        knowledge_bases = courseclass.knowledge_bases
        if not knowledge_bases:
            logger.warning(f"课程班未关联知识库: courseclass_id={courseclass.id}")
            return jsonify(code=400, message="课程班未关联任何知识库"), 400
            
        db_names = [kb.stored_basename for kb in knowledge_bases]
        logger.info(f"使用知识库: {db_names}")

        # 5. 获取课前预习题目
        student_feedback = get_pre_class_questions_as_feedback(data['course_id'])
        logger.debug(f"获取到学生反馈: {student_feedback[:100]}...")

        # 6. 构建生成参数（使用课程目标和内容）
        generation_input = f"""
        # 课程目标:
        {course.objectives}
        
        # 课程内容:
        {course.content}
        """

        # 7. 异步生成教学方案
        plan_content = await generate_teaching_plans_async(
            course_content=generation_input,  # 使用课程目标和内容作为输入
            student_feedback=student_feedback,
            db_names=db_names,
            similarity_threshold=0.7,
            chunk_cnt=5
        )
        logger.info("教学方案生成成功")

        # 8. 创建数据库记录
        new_design = TeachingDesign(
            course_id=data['course_id'],
            creator_id=current_user.id,
            title=data.get('title', f"{course.name}教学设计"),
            input=generation_input  # 记录使用的原始输入
        )
        db.session.add(new_design)
        db.session.flush()

        # 9. 保存版本
        version = await save_teaching_design_version_async(new_design, plan_content)
        logger.info(f"创建教学设计版本: version_id={version.id}")
        
        # 10. 设置当前版本
        new_design.current_version_id = version.id
        db.session.commit()
        logger.info(f"教学设计创建成功: design_id={new_design.id}")

        # 11. 返回响应
        return jsonify({
            "code": 200,
            "data": {
                "design_id": new_design.id,
                "version_id": version.id,
                "title": new_design.title,
                "course_name": course.name,
                "objectives_used": course.objectives[:200] + "..." if len(course.objectives) > 200 else course.objectives,
                "content_used": course.content[:200] + "..." if len(course.content) > 200 else course.content,
                "courseclass": courseclass.name,
                "knowledge_bases_used": [kb.name for kb in knowledge_bases]
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.exception("创建教学设计失败")
        return jsonify(code=500, message="服务器内部错误"), 500

@teaching_design_bp.route('/<int:design_id>/versions', methods=['GET'])
def get_design_versions(design_id):
    """查询单个教学设计的所有教学设计版本"""
    try:
        # 1. 基础验证
        current_user = get_current_user()

        # 2. 查询教学设计
        design = TeachingDesign.query.get(design_id)
        if not design:
            return jsonify(code=404, message="教学设计不存在"), 404

        # 3. 权限验证（教师只能查看自己课程的）
        if not design.is_public and current_user.role == 'teacher' and not is_teacher_of_course(design.course_id):
            return jsonify(code=403, message="无访问权限"), 403

        # 4. 查询所有版本（按版本号排序）
        versions = TeachingDesignVersion.query.filter_by(
            design_id=design_id
        ).order_by(TeachingDesignVersion.version).all()

        # 5. 构建响应数据
        versions_data = []
        for version in versions:
            try:
                content = json.loads(version.content) if version.content else None
            except json.JSONDecodeError:
                content = version.content
            
            versions_data.append({
                "id": version.id,
                "version": version.version,
                "content": content,
                "recommendation_score": version.recommendation_score,
                "created_at": version.created_at.isoformat() if version.created_at else None,
                "updated_at": version.updated_at.isoformat() if version.updated_at else None,
                "author_id": version.author_id
            })

        return jsonify(
            code=200,
            message="获取成功",
            data={
                "design_id": design.id,
                "title": design.title,
                "current_version_id": design.current_version_id,
                "versions": versions_data
            }
        ), 200

    except Exception as e:
        logger.error(f"获取教学设计版本失败: {str(e)}", exc_info=True)
        return jsonify(code=500, message="服务器内部错误"), 500

@teaching_design_bp.route('/mydesigns', methods=['GET'])
def get_my_designs():
    """
    查询当前登录教师的所有教学设计及其生成时间与更新时间
    """
    try:
        # 1. 验证用户是否登录且为教师
        current_user = get_current_user()
        if not current_user or current_user.role != 'teacher':
            return jsonify(code=403, message="无访问权限"), 403

        # 2. 查询该教师创建的所有教学设计
        designs = TeachingDesign.query.filter_by(creator_id=current_user.id).all()

        # 3. 构建响应数据
        designs_data = []
        for design in designs:
            design_data = {
                "design_id": design.id,
                "title": design.title,
                "default_version_id": design.current_version_id,
                "course_id": design.course_id,
                "created_at": design.created_at.isoformat() if design.created_at else None,
                "updated_at": design.updated_at.isoformat() if design.updated_at else None
            }
            designs_data.append(design_data)

        return jsonify(code=200, message="查询成功", data=designs_data), 200

    except Exception as e:
        logger.error(f"查询教学设计失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500

@teaching_design_bp.route('/versions/<int:version_id>', methods=['GET'])
def get_teaching_design_version(version_id):
    """
    根据教学设计版本ID查询版本内容
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()

        # 2. 查询教学设计版本
        version = TeachingDesignVersion.query.get(version_id)
        if not version:
            return jsonify(code=404, message="教学设计版本不存在"), 404
        design =TeachingDesign.query.get(version.design_id)
        # 3. 权限验证（教师只能查看自己创建的版本）
        if not design.is_public and current_user.role == 'teacher' and version.author_id != current_user.id:
            return jsonify(code=403, message="无访问权限"), 403
        version_data = {
            "id": version.id,
            "design_id": version.design_id,
            "version": version.version,
            "plan_content": version.content,
            "recommendation_score": version.recommendation_score,
            "level": version.level,
            "created_at": version.created_at.isoformat() if version.created_at else None,
            "updated_at": version.updated_at.isoformat() if version.updated_at else None,
            "author_id": version.author_id
        }

        return jsonify(code=200, message="查询成功", data=version_data), 200

    except Exception as e:
        logger.error(f"查询教学设计版本失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500

@teaching_design_bp.route('/course/<int:course_id>/designs', methods=['GET'])
def get_course_designs(course_id):
    """
    查询单个课程的所有教学设计
    """
    try:
        # 1. 获取当前用户
        current_user = get_current_user()
        
        # 2. 查询课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify(code=404, message="课程不存在"), 404

        # 3. 查询该课程的所有教学设计
        designs = TeachingDesign.query.filter_by(course_id=course_id).all()

        # 4. 构建响应数据（同时检查权限）
        designs_data = []
        for design in designs:
            # 权限检查：如果是教师，只能查看自己创建的教学设计
            if current_user.role == 'teacher' and design.creator_id != current_user.id:
                continue  # 跳过非自己创建的设计
                
            design_data = {
                "design_id": design.id,
                "title": design.title,
                "default_version_id": design.current_version_id,
                "creator_id": design.creator_id,
                "created_at": design.created_at.isoformat() if design.created_at else None,
                "is_public": design.is_public,
                "is_recommended": design.is_recommended
            }
            designs_data.append(design_data)

        return jsonify(code=200, message="查询成功", data=designs_data), 200

    except Exception as e:
        logger.error(f"查询课程教学设计失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500
    
    
#修改单个教学设计的基本信息
@teaching_design_bp.route('/design/<int:design_id>', methods=['PUT'])
def update_teaching_design(design_id):
    """
    修改单个教学设计的基本信息
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()

        # 2. 查询教学设计
        design = TeachingDesign.query.get(design_id)
        if not design:
            return jsonify(code=404, message="教学设计不存在"), 404
        # 3. 权限验证（教师只能修改自己创建的教学设计）
        if current_user.role != 'teacher' or (current_user.role == 'teacher' and design.creator_id != current_user.id):
            return jsonify(code=403, message="无操作权限"), 403
        
        # 4. 获取请求数据并更新
        data = request.get_json()
        if not data:
            return jsonify(code=400, message="缺少必要参数"), 400

        # 只允许修改 title 和 current_version_id
        if 'title' in data:
            design.title = data['title']
        if 'default_version_id' in data:
            design.current_version_id = data['default_version_id']

        db.session.commit()

        return jsonify(code=200, message="更新成功", data={"design_id": design.id, "title": design.title, "default_version_id": design.current_version_id}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新教学设计失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500

@teaching_design_bp.route('/design/<int:design_id>/version/<int:version_id>', methods=['PUT'])
def update_teaching_design_version(design_id, version_id):
    """
    修改单个教学设计版本的详细信息
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()

        # 2. 查询教学设计和版本
        design = TeachingDesign.query.get(design_id)
        if not design:
            return jsonify(code=404, message="教学设计不存在"), 404

        version = TeachingDesignVersion.query.get(version_id)
        if not version or version.design_id != design.id:
            return jsonify(code=404, message="教学设计版本不存在"), 404

        # 3. 权限验证（教师只能修改自己创建的版本）
        if current_user.role == 'teacher' and version.author_id != current_user.id:
            return jsonify(code=403, message="无操作权限"), 403

        # 4. 获取请求数据并更新
        data = request.get_json()
        if not data:
            return jsonify(code=400, message="缺少必要参数"), 400

        # 尝试解析当前版本的 content 为 JSON
        try:
            current_content = json.loads(version.content) if version.content else {}
        except json.JSONDecodeError:
            current_content = {}

        # 如果传入了 plan_content 数据，更新其中的 plan_content 部分
        if 'plan_content' in data:
            current_content['plan_content'] = data['plan_content']

        # 如果传入了 analysis 数据，更新其中的 analysis 部分
        if 'analysis' in data:
            current_content['analysis'] = data['analysis']

        # 将更新后的 content 重新序列化为 JSON
        version.content = json.dumps(current_content)

        # 如果传入了其他字段，直接更新
        if 'recommendation_score' in data:
            version.recommendation_score = data['recommendation_score']
        if 'level' in data:
            version.level = data['level']

        db.session.commit()

        # 返回更新后的版本信息
        return jsonify(code=200, message="更新成功", data={
            "version_id": version.id,
            "plan_content": current_content.get("plan_content", "未设置教学设计内容"),
            "analysis": current_content.get("analysis", "未设置教学分析"),
            "recommendation_score": version.recommendation_score,
            "level": version.level
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新教学设计版本失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500

@teaching_design_bp.route('/design/<int:design_id>', methods=['GET'])
def get_teaching_design(design_id):
    """
    查询单个教学设计的详细信息
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()

        # 2. 查询教学设计
        design = TeachingDesign.query.get(design_id)
        if not design:
            return jsonify(code=404, message="教学设计不存在"), 404

        # 3. 权限验证（教师只能查询自己创建的教学设计，管理员可以查询所有）
        if current_user.role == 'teacher' and design.creator_id != current_user.id:
            return jsonify(code=403, message="无操作权限"), 403

        # 4. 构造返回数据
        design_data = {
            "design_id": design.id,
            "title": design.title,
            "course_id": design.course_id,
            "creator_id": design.creator_id,
            "default_version_id": design.current_version_id,
            "created_at": design.created_at.isoformat() if design.created_at else None,
            "updated_at": design.updated_at.isoformat() if design.updated_at else None,
            "is_public": design.is_public,
            "is_recommended": design.is_recommended,
        }

        return jsonify(code=200, message="查询成功", data=design_data), 200

    except Exception as e:
        logger.error(f"查询教学设计失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500
    
@teaching_design_bp.route('/course/<int:source_course_id>/migrate/<int:target_course_id>', methods=['POST'])
def migrate_course_designs(source_course_id, target_course_id):
    """
    将一个课程的所有教学设计及其版本迁移到另一个课程
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()

        # 2. 查询源课程和目标课程
        source_course = Course.query.get(source_course_id)
        target_course = Course.query.get(target_course_id)
        if not source_course:
            return jsonify(code=404, message="源课程不存在"), 404
        if not target_course:
            return jsonify(code=404, message="目标课程不存在"), 404

        # 3. 权限验证（教师只能迁移自己创建的教学设计）
        if current_user.role == 'teacher' and not is_teacher_of_course(source_course_id):
            return jsonify(code=403, message="无操作权限"), 403

        # 4. 查询源课程的所有教学设计
        designs = TeachingDesign.query.filter_by(course_id=source_course_id).all()

        # 5. 复制教学设计及其版本到目标课程
        new_designs = []
        for design in designs:
            # 创建新的教学设计
            new_design = TeachingDesign(
                course_id=target_course_id,
                creator_id=current_user.id,
                title=design.title,
                current_version_id=None  # 新的教学设计暂无当前版本
            )
            db.session.add(new_design)
            db.session.flush()

            # 复制版本
            versions = TeachingDesignVersion.query.filter_by(design_id=design.id).all()
            new_versions = []
            for version in versions:
                new_version = TeachingDesignVersion(
                    design_id=new_design.id,
                    version=version.version,
                    content=version.content,
                    author_id=current_user.id,
                    level=version.level,
                    recommendation_score=version.recommendation_score
                )
                db.session.add(new_version)
                new_versions.append(new_version)

            # 设置新教学设计的当前版本（选择推荐指数最高的）
            if new_versions:
                best_version = max(new_versions, key=lambda v: v.recommendation_score)
                new_design.current_version_id = best_version.id

            new_designs.append(new_design)

        # 提交所有新创建的教学设计和版本到数据库
        db.session.commit()

        # 6. 返回响应
        return jsonify(code=200, message="迁移成功", data=[{"design_id": d.id, "title": d.title} for d in new_designs]), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"迁移教学设计失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500

@teaching_design_bp.route('/generatemindmap/<int:design_id>', methods=['POST'])
async def generate_and_store_mindmap(design_id):
    """异步生成思维导图并存储"""
    try:
        # 1. 基础验证
        current_user = get_current_user()
        if not current_user:
            return jsonify(code=401, message="请先登录"), 401

        # 2. 查询教学设计
        design = TeachingDesign.query.get(design_id)
        if not design:
            return jsonify(code=404, message="教学设计不存在"), 404

        # 3. 权限验证（教师只能操作自己创建的教学设计）
        if current_user.role == 'teacher' and design.creator_id != current_user.id:
            return jsonify(code=403, message="无操作权限"), 403

        # 4. 获取默认版本的教学设计内容
        default_version = next(
            (v for v in design.versions if v.id == design.current_version_id),
            None
        )
        if not default_version or not default_version.content:
            return jsonify(code=400, message="默认版本不存在或内容为空"), 400

        # 尝试解析默认版本的 content 为 JSON
        try:
            version_content = json.loads(default_version.content)
        except json.JSONDecodeError:
            return jsonify(code=400, message="默认版本内容格式错误"), 400

        # 5. 调用函数生成思维导图
        mind_map_json = generate_knowledge_mind_map(version_content.get('plan_content', ''))

        # 6. 存储思维导图到 MindMapNode 表，并获取带有 node_id 的思维导图
        stored_mind_map = await asyncio.to_thread(store_and_adjust_mind_map, design.id, mind_map_json)

        # 7. 将调整后的 JSON 存储到 TeachingDesign 的 mindmap 字段
        design.mindmap = json.dumps(stored_mind_map)
        db.session.commit()

        return jsonify(code=200, message="思维导图生成并存储成功", data={
            "design_id": design.id,
            "mind_map": stored_mind_map
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"生成并存储思维导图失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500
    
def store_and_adjust_mind_map(teachingdesignid, mind_map):
    """存储思维导图到 MindMapNode 表，并调整节点 id 为数据库生成的 id"""
    # 清除现有的 MindMapNode 记录（如果需要保留历史记录，可以注释掉这行）
    top_level_nodes = MindMapNode.query.filter_by(teachingdesignid=teachingdesignid, parent_node_id=None).all()
    for node in top_level_nodes:
        db.session.delete(node)
    db.session.commit()  # 提交删除操作

    # 递归存储节点并调整结构
    adjusted_map = store_and_get_adjusted_map(teachingdesignid, None, mind_map)

    return adjusted_map

def store_and_get_adjusted_map(teachingdesignid, parent_node_id, node_data):
    """递归存储节点并获取调整后的节点数据"""
    if not isinstance(node_data, dict):
        return node_data

    # 创建当前节点
    new_node = MindMapNode(
        teachingdesignid=teachingdesignid,
        node_name=node_data.get("name", "未命名节点"),
        node_content=node_data.get("content", ""),
        parent_node_id=parent_node_id,
        is_leaf=True  # 默认为叶子节点
    )
    db.session.add(new_node)
    db.session.flush()  # 立即插入以获取新生成的 ID

    # 检查是否为叶子节点
    if "children" in node_data and isinstance(node_data["children"], list) and len(node_data["children"]) > 0:
        new_node.is_leaf = False
        db.session.commit()

    # 递归存储子节点并调整结构
    adjusted_node = {
        "data": {  # 将节点信息包裹在 data 字段中
            "id": new_node.id,
            "text": new_node.node_name,
            "note": new_node.node_content
        },
        "children": []
    }

    if "children" in node_data and isinstance(node_data["children"], list):
        for child_data in node_data["children"]:
            adjusted_child = store_and_get_adjusted_map(teachingdesignid, new_node.id, child_data)
            if adjusted_child:
                adjusted_node["children"].append(adjusted_child)

    return adjusted_node

# 智能更新思维导图数据
@teaching_design_bp.route('/updatemindmap/<int:design_id>', methods=['POST'])
def update_mind_map(design_id):
    """
    智能更新思维导图数据：
    1. 对含id的节点验证并更新内容
    2. 对不含id的节点创建新记录
    3. 自动维护父子节点关系
    4. 生成完整思维导图存储
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()

        design = TeachingDesign.query.get(design_id)
        if not design:
            return jsonify(code=404, message="教学设计不存在"), 404

        if current_user.role == 'teacher' and design.creator_id != current_user.id:
            return jsonify(code=403, message="无操作权限"), 403

        data = request.get_json()
        if not data or 'mind_map' not in data:
            return jsonify(code=400, message="缺少思维导图数据"), 400

        # 2. 获取现有节点映射表（用于快速查找）
        existing_nodes = {
            node.id: node
            for node in MindMapNode.query.filter_by(teachingdesignid=design_id).all()
        }

        # 3. 递归处理节点树
        def process_node(node_data, parent_id=None):
            # 提取 data 字段中的信息
            node_info = node_data.get('data', {})
            
            # 处理已有节点
            if 'id' in node_info and node_info['id'] in existing_nodes:
                node = existing_nodes[node_info['id']]

                # 验证节点归属
                if node.teachingdesignid != design_id:
                    raise ValueError("节点不属于当前教学设计")

                # 更新变更字段
                update_flag = False
                if node.node_name != node_info.get('text'):
                    node.node_name = node_info.get('text', node.node_name)
                    update_flag = True
                if node.node_content != node_info.get('note'):
                    node.node_content = node_info.get('note', node.node_content)
                    update_flag = True
                if node.parent_node_id != parent_id:
                    node.parent_node_id = parent_id
                    update_flag = True

                if update_flag:
                    db.session.add(node)

                node_id = node.id
                is_new = False
            # 创建新节点
            else:
                is_leaf = not bool(node_data.get('children', []))
                new_node = MindMapNode(
                    teachingdesignid=design_id,
                    node_name=node_info.get('text', '未命名节点'),
                    node_content=node_info.get('note', ''),
                    parent_node_id=parent_id,
                    is_leaf=is_leaf
                )
                db.session.add(new_node)
                db.session.flush()
                node_id = new_node.id
                is_new = True
                existing_nodes[node_id] = new_node  # 加入映射表

            # 处理子节点
            children_data = node_data.get('children', [])
            processed_children = []
            for child_data in children_data:
                child_node = process_node(child_data, node_id)
                processed_children.append(child_node)

            # 返回处理后的节点结构
            return {
                "data": {  # 将节点信息包裹在 data 字段中
                    "id": node_id,
                    "text": node_info.get('text', ''),  # 使用 text 字段
                    "note": node_info.get('note', ''),  # 使用 note 字段
                },
                "children": processed_children
            }

        # 4. 开始处理（先清除已删除的节点关系）
        MindMapNode.query.filter_by(teachingdesignid=design_id).update({'parent_node_id': None})
        db.session.flush()

        # 5. 构建新树结构
        mind_map_data = data['mind_map']
        updated_map = process_node(mind_map_data)

        # 6. 清理孤立节点（可选）
        updated_ids = set()
        def collect_ids(node):
            updated_ids.add(node['data']['id'])
            for child in node.get('children', []):
                collect_ids(child)
        collect_ids(updated_map)

        # 删除未被引用的旧节点
        nodes_to_delete = MindMapNode.query.filter(
            MindMapNode.teachingdesignid == design_id,
            ~MindMapNode.id.in_(updated_ids)
        ).with_entities(MindMapNode.id).all()

        # 删除这些节点对应的 question 记录
        question_ids_to_delete = [node.id for node in nodes_to_delete]
        Question.query.filter(
            Question.knowledge_point_id.in_(question_ids_to_delete)
        ).delete(synchronize_session=False)

        # 删除未被引用的 mind_map_node 记录
        MindMapNode.query.filter(
            MindMapNode.teachingdesignid == design_id,
            ~MindMapNode.id.in_(updated_ids)
        ).delete(synchronize_session=False)

        # 7. 更新教学设计记录
        design.mindmap = json.dumps(updated_map)
        db.session.commit()

        # 8. 重新查询数据库以获取最新的节点状态
        existing_nodes_after_commit = {
            node.id: node
            for node in MindMapNode.query.filter_by(teachingdesignid=design_id).all()
        }

        # 9. 计算统计信息
        updated_nodes_count = len([n for n in existing_nodes_after_commit.values() if n.id in updated_ids])
        new_nodes_count = len(updated_ids) - len(existing_nodes_after_commit)

        return jsonify(code=200, message="更新成功", data={
            "design_id": design.id,
            "mind_map": updated_map,
            "stats": {
                "updated_nodes": updated_nodes_count,
                "new_nodes": new_nodes_count
            }
        }), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify(code=400, message=str(e)), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"思维导图更新失败: {str(e)}", exc_info=True)
        return jsonify(code=500, message="服务器内部错误"), 500

@teaching_design_bp.route('/<int:design_id>/generate_mindmap', methods=['POST'])
def generate_and_store_mind_map(design_id):
    """将单个教学设计的所有节点组成思维导图并存储"""
    try:
        # 1. 基础验证
        current_user = get_current_user()

        # 2. 查询教学设计
        design = TeachingDesign.query.get(design_id)
        if not design:
            return jsonify(code=404, message="教学设计不存在"), 404

        # 3. 权限验证（教师只能操作自己创建的教学设计）
        if current_user.role == 'teacher' and design.creator_id != current_user.id:
            return jsonify(code=403, message="无操作权限"), 403

        # 4. 查询该教学设计的所有知识点
        top_level_nodes = MindMapNode.query.filter_by(
            teachingdesignid=design_id, 
            parent_node_id=None
        ).all()

        # 5. 递归构建思维导图
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
        # 6. 构建完整的思维导图
        mind_map = []
        for root_node in top_level_nodes:
            mind_map.append(build_mind_map(root_node))

        # 7. 将思维导图存储到 TeachingDesign 的 mindmap 字段
        design.mindmap = json.dumps(mind_map, ensure_ascii=False)
        db.session.commit()

        return jsonify(code=200, message="思维导图生成并存储成功", data={
            "design_id": design.id,
            "mind_map": mind_map
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"生成并存储思维导图失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500
    
@teaching_design_bp.route('/teaching-design/<int:design_id>/mindmap', methods=['GET'])
def get_teaching_design_mindmap(design_id):
    """获取单个教学设计的思维导图接口"""
    try:
        # 获取当前登录用户
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # 查询教学设计是否存在
        design = TeachingDesign.query.get(design_id)
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
            return jsonify({'error': 'You do not have permission to access this teaching design'}), 403

        # 判断是否在课后习题截止时间之后，且思维导图是否需要更新
        mindmap_needs_update = True

        # 如果当前时间在课后习题截止时间之后
        if course.post_class_deadline and datetime.utcnow() > course.post_class_deadline:
            # 检查是否已更新过思维导图
            if not design.mindmap_updated_at or design.mindmap_updated_at < course.post_class_deadline:
                mindmap_needs_update = True

         # 如果需要更新思维导图
        if mindmap_needs_update:
            # 修改后的递归构建函数
            def build_mind_map_with_colors(node, is_root=False):
                node_data = {
                    "data": {
                        "id": node.id,
                        "text": node.node_name,
                        "note": node.node_content
                    },
                    "children": []
                }

                # 仅非根节点添加fillColor字段
                if not is_root:
                    node_data["data"]["fillColor"] = calculate_node_color(node.id)

                # 递归处理子节点（自动标记为非根节点）
                for child in node.children:
                    node_data["children"].append(build_mind_map_with_colors(child))
                
                return node_data

            # 获取并构建顶级节点（标记为根节点）
            top_level_nodes = MindMapNode.query.filter_by(
                teachingdesignid=design_id,
                parent_node_id=None
            ).all()

            # 构建完整的思维导图结构
            mind_map_with_colors = [
                build_mind_map_with_colors(root_node, is_root=True)
                for root_node in top_level_nodes
            ]
            for root_node in top_level_nodes:
                mind_map_with_colors.append(build_mind_map_with_colors(root_node, is_root=True))

            # 将更新后的思维导图存储到 TeachingDesign 的 mindmap 字段
            design.mindmap = json.dumps(mind_map_with_colors, ensure_ascii=False)
            design.mindmap_updated_at = datetime.utcnow()  # 更新 mindmap_updated_at 字段
            db.session.commit()

        # 返回思维导图
        return jsonify({
            'mindmap': json.loads(design.mindmap) if design.mindmap else None,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@teaching_design_bp.route('/design/<int:design_id>/set_visibility', methods=['PUT'])
def set_design_visibility(design_id):
    """设置教案可见性"""
    try:
        # 1. 验证用户
        current_user = get_current_user()
            
        if current_user.role != 'teacher':
            logger.error(f"用户无权限: {current_user.id}")
            return jsonify(code=403, message="无操作权限"), 403

        # 2. 获取教学设计
        design = TeachingDesign.query.get(design_id)
        
        if not design:
            logger.error(f"教学设计不存在: {design_id}")
            return jsonify(code=404, message="教学设计不存在"), 404
        
        # 3. 验证是否是作者
        if design.creator_id != current_user.id:
            logger.error(f"用户{current_user.id}尝试操作他人教学设计{design_id}")
            return jsonify(code=403, message="只能操作自己的教学设计"), 403

        # 4. 获取请求数据
        data = request.get_json()
        if not data:
            logger.error("请求数据为空")
            return jsonify(code=400, message="缺少必要参数"), 400

        # 记录接收到的数据
        logger.info(f"接收到的更新数据: {data}")

        # 5. 更新状态
        if 'is_public' in data and 'is_recommended' in data:
            design.is_public = bool(data['is_public'])
            logger.info(f"更新is_public为: {design.is_public}")
            if data['is_recommended']:
                design.is_recommended = True
                design.recommend_time = datetime.utcnow()
                logger.info("设置为推荐教学设计")
            else:
                design.is_recommended = False
                design.recommend_time = None
                logger.info("取消推荐教学设计")

        db.session.commit()
        logger.info("数据库更新成功")

        return jsonify(code=200, message="状态更新成功", data={
            "design_id": design.id,
            "is_public": design.is_public,
            "is_recommended": design.is_recommended,
            "recommend_time": design.recommend_time.isoformat() if design.recommend_time else None
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新教学设计可见性失败: {str(e)}", exc_info=True)
        return jsonify(code=500, message=f"服务器内部错误: {str(e)}"), 500



@teaching_design_bp.after_request
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
            'body': request.get_json(silent=True) if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] else None,
            'status': response.status_code,
            'timestamp': datetime.now().isoformat()
        }
    )
    return response