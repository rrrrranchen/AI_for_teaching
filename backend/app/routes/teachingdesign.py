import asyncio
import os
import uuid
from venv import logger
from bson import ObjectId
from flask import Blueprint, app, current_app, json, make_response, redirect, render_template, request, jsonify, send_file, session
from jwt import InvalidKeyError
from sqlalchemy import func, select
from app.utils.database import db
from app.models.user import User
from app.models.courseclass import Courseclass
from app.models.relationship import teacher_class
from app.models.course import Course
from app.models.teaching_design import TeachingDesign
from app.models.teachingdesignversion import TeachingDesignVersion
from app.models.question import Question
from app.services.lesson_plan import generate_post_class_questions, generate_teaching_plans

teachingdesign_bp=Blueprint('teachingdesign',__name__)

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

def is_logged_in():
    """检查用户是否登录"""
    return 'user_id' in session

def get_current_user():
    """获取当前登录用户"""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

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

# 异步生成教学方案
async def generate_teaching_plans_async(course_content, student_feedback):
    # 模拟异步生成教学方案的过程
    await asyncio.sleep(1)  # 模拟耗时操作
    # 假设 generate_teaching_plans 是同步函数，我们在这里调用它
    return generate_teaching_plans(course_content=course_content, student_feedback=student_feedback)

# 异步保存教学设计版本
async def save_teaching_design_versions_async(new_design, teaching_plans):
    versions = []
    for i, plan in enumerate(teaching_plans['plans'], 1):
        version = TeachingDesignVersion(
            design_id=new_design.id,
            version=f'{i}',
            content=json.dumps({
                'plan_content': plan['content'],
                'analysis': plan.get('analysis', '')
            }),
            recommendation_score=plan['recommendation'],
            level=plan['level'],
            author_id=new_design.creator_id
        )
        versions.append(version)
    await asyncio.gather(*[asyncio.to_thread(db.session.add, version) for version in versions])
    return versions

# 异步设置当前版本
async def set_current_version_async(new_design, versions):
    best_version = max(versions, key=lambda v: v.recommendation_score)
    new_design.current_version_id = best_version.id
    await asyncio.to_thread(db.session.commit)

# 异步创建教学设计
# 异步创建教学设计
@teachingdesign_bp.route('/createteachingdesign', methods=['POST'])
async def create_teaching_design():
    try:
        # 1. 身份验证和基础校验
        current_user = get_current_user()
        if not current_user or current_user.role != 'teacher':
            return jsonify(code=403, message="无操作权限"), 403

        data = request.get_json()
        if not data or 'course_id' not in data:
            return jsonify(code=400, message="缺少必要参数"), 400

        # 2. 自动获取课前预习题目作为学生反馈
        student_feedback = get_pre_class_questions_as_feedback(data['course_id'])

        # 3. 异步生成教学方案
        teaching_plans = await generate_teaching_plans_async(
            course_content=data.get('course_content', ''),
            student_feedback=student_feedback
        )

        # 4. 创建数据库记录
        new_design = TeachingDesign(
            course_id=data['course_id'],
            creator_id=current_user.id,
            title=data.get('title', '未命名设计'),
            input=data.get('course_content', '')  # 将 course_content 记录到 input 字段
        )
        db.session.add(new_design)
        db.session.flush()

        # 5. 异步保存生成的版本
        versions = await save_teaching_design_versions_async(new_design, teaching_plans)

        # 6. 异步设置当前版本
        await set_current_version_async(new_design, versions)

        # 7. 返回响应
        return jsonify({
            "code": 200,
            "data": {
                "design_id": new_design.id,
                "feedback_used": student_feedback[:200] + "..." if len(student_feedback) > 200 else student_feedback,
                "versions": [ {
                    "id": v.id,
                    "level": v.level,
                    "recommendation": v.recommendation_score
                } for v in versions ]
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建教学设计失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500

#查询单个教学设计的所有教学设计版本
@teachingdesign_bp.route('/<int:design_id>/versions', methods=['GET'])
def get_design_versions(design_id):
 
    try:
        # 1. 基础验证
        current_user = get_current_user()
        if not current_user:
            return jsonify(code=401, message="请先登录"), 401

        # 2. 查询教学设计
        design = TeachingDesign.query.get(design_id)
        if not design:
            return jsonify(code=404, message="教学设计不存在"), 404

        # 3. 权限验证（教师只能查看自己课程的）
        if current_user.role == 'teacher' and not is_teacher_of_course(design.course_id):
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


#查询所属当前用户的所有教学设计
@teachingdesign_bp.route('/mydesigns', methods=['GET'])
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
                "course_id": design.course_id,
                "created_at": design.created_at.isoformat() if design.created_at else None,
                "updated_at": design.updated_at.isoformat() if design.updated_at else None
            }
            designs_data.append(design_data)

        return jsonify(code=200, message="查询成功", data=designs_data), 200

    except Exception as e:
        logger.error(f"查询教学设计失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500

#查询单个教学设计版本
@teachingdesign_bp.route('/versions/<int:version_id>', methods=['GET'])
def get_teaching_design_version(version_id):
    """
    根据教学设计版本ID查询版本内容
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()
        if not current_user:
            return jsonify(code=401, message="请先登录"), 401

        # 2. 查询教学设计版本
        version = TeachingDesignVersion.query.get(version_id)
        if not version:
            return jsonify(code=404, message="教学设计版本不存在"), 404

        # 3. 权限验证（教师只能查看自己创建的版本）
        if current_user.role == 'teacher' and version.author_id != current_user.id:
            return jsonify(code=403, message="无访问权限"), 403

        # 4. 构建响应数据
        try:
            # 尝试解析 content 字段为 JSON
            content = json.loads(version.content) if version.content else {}
        except json.JSONDecodeError:
            # 如果 content 不是有效的 JSON 格式，则返回原始内容
            content = {"error": "内容格式错误", "raw_content": version.content}
        plan_content = content.get("plan_content", "未设置教学设计内容")
        analysis = content.get("analysis", "未设置教学分析")

        version_data = {
            "id": version.id,
            "design_id": version.design_id,
            "version": version.version,
            "plan_content": plan_content,
            "analysis": analysis,
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

#查询单个课程的所有教学设计
@teachingdesign_bp.route('/course/<int:course_id>/designs', methods=['GET'])
def get_course_designs(course_id):
    """
    查询单个课程的所有教学设计
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()
        if not current_user:
            return jsonify(code=401, message="请先登录"), 401

        # 2. 查询课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify(code=404, message="课程不存在"), 404

        # 3. 查询该课程的所有教学设计
        designs = TeachingDesign.query.filter_by(course_id=course_id).all()

        # 4. 构建响应数据
        designs_data = []
        for design in designs:
            design_data = {
                "design_id": design.id,
                "title": design.title,
                "creator_id": design.creator_id,
                "created_at": design.created_at.isoformat() if design.created_at else None
            }
            designs_data.append(design_data)

        return jsonify(code=200, message="查询成功", data=designs_data), 200

    except Exception as e:
        logger.error(f"查询课程教学设计失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500

#修改单个教学设计的基本信息
@teachingdesign_bp.route('/design/<int:design_id>', methods=['PUT'])
def update_teaching_design(design_id):
    """
    修改单个教学设计的基本信息
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()
        if not current_user:
            return jsonify(code=401, message="请先登录"), 401

        # 2. 查询教学设计
        design = TeachingDesign.query.get(design_id)
        if not design:
            return jsonify(code=404, message="教学设计不存在"), 404

        # 3. 权限验证（教师只能修改自己创建的教学设计）
        if current_user.role == 'teacher' and design.creator_id != current_user.id:
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

#修改单个教学设计版本的基本信息
@teachingdesign_bp.route('/design/<int:design_id>/version/<int:version_id>', methods=['PUT'])
def update_teaching_design_version(design_id, version_id):
    """
    修改单个教学设计版本的详细信息
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()
        if not current_user:
            return jsonify(code=401, message="请先登录"), 401

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


@teachingdesign_bp.route('/design/<int:design_id>', methods=['GET'])
def get_teaching_design(design_id):
    """
    查询单个教学设计的详细信息
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()
        if not current_user:
            return jsonify(code=401, message="请先登录"), 401

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
            "updated_at": design.updated_at.isoformat() if design.updated_at else None
        }

        return jsonify(code=200, message="查询成功", data=design_data), 200

    except Exception as e:
        logger.error(f"查询教学设计失败: {str(e)}")
        return jsonify(code=500, message="服务器内部错误"), 500
    

#将一个课程中的教学设计及其所有版本迁移到另一个课程
@teachingdesign_bp.route('/course/<int:source_course_id>/migrate/<int:target_course_id>', methods=['POST'])
def migrate_course_designs(source_course_id, target_course_id):
    """
    将一个课程的所有教学设计及其版本迁移到另一个课程
    """
    try:
        # 1. 基础验证
        current_user = get_current_user()
        if not current_user:
            return jsonify(code=401, message="请先登录"), 401

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


