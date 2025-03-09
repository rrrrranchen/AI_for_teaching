from flask import Blueprint, app, request, jsonify, session, render_template
from app.models.lesson_plan import LessonPlan
from app.models.user import User
from app.services.ai_service import generate_lesson_plan
from app.utils.database import db

lesson_plan_bp = Blueprint('lesson_plan', __name__)

@lesson_plan_bp.route('/create', methods=['POST'])
def create_lesson_plan():
    """
    创建教学计划接口（使用 Session 验证）
    """
    # ----------------------
    # 身份验证阶段
    # ----------------------
    teacher_id = session.get('user_id')
    if not teacher_id:
        return jsonify({
            "message": "Unauthorized",
            "error": "auth_error"
        }), 401

    # ----------------------
    # 数据验证阶段
    # ----------------------
    data = request.get_json()
    
    # 检查请求体是否为合法JSON
    if not data:
        return jsonify({
            "message": "Missing JSON request body",
            "error": "bad_request"
        }), 400
    
    
    required_fields = ['title']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({
            "message": f"Missing required fields: {', '.join(missing_fields)}",
            "error": "validation_error"
        }), 400
    
    # 清理输入数据
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    generated_by = data.get('generated_by', 'manual')
    
    # 验证title有效性
    if not title:
        return jsonify({
            "message": "Title cannot be empty",
            "error": "validation_error"
        }), 400
    
    # 验证生成方式合法性
    if generated_by not in ['manual', 'AI']:
        return jsonify({
            "message": "Invalid generated_by value (allowed: 'manual' or 'AI')",
            "error": "validation_error"
        }), 400
    
    # ----------------------
    # 业务逻辑处理阶段
    # ----------------------
    try:
        # 检查用户是否存在
        teacher = User.query.get(teacher_id)
        if not teacher:
            return jsonify({
                "message": "Teacher account not found",
                "error": "auth_error"
            }), 404
        
        # AI生成内容处理
        content = data.get('content', '')
        if generated_by == 'AI':
            try:
                content = generate_lesson_plan(title, description)
            except Exception as e:
                # 记录AI服务错误
                app.logger.error(f"AI service error: {str(e)}")
                return jsonify({
                    "message": "Failed to generate AI content",
                    "error": "ai_service_error"
                }), 503
        
        # 创建教学计划对象
        new_plan = LessonPlan(
            teacher_id=teacher_id,
            title=title,
            description=description,
            content=content,
            status=data.get('status', 'draft'),
            generated_by=generated_by
        )
        
        # 数据库操作
        db.session.add(new_plan)
        db.session.commit()
        
        return jsonify({
            "message": "Lesson plan created successfully",
            "plan": new_plan.to_dict()
        }), 201
        
    except Exception as e:
        # 全局异常捕获
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "message": "Internal server error",
            "error": "server_error"
        }), 500

@lesson_plan_bp.route('/all', methods=['GET'])
def get_all_lesson_plans():
    """
    获取当前用户的所有教学计划（使用 Session 验证）
    """
    # 从 session 中获取用户 ID
    teacher_id = session.get('user_id')
    if not teacher_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # 查询教学计划
    lesson_plans = LessonPlan.query.filter_by(teacher_id=teacher_id).all()
    result = [plan.to_dict() for plan in lesson_plans]
    return jsonify({'lesson_plans': result}), 200

@lesson_plan_bp.route('/<int:plan_id>', methods=['GET'])
def get_lesson_plan(plan_id):
    """
    获取单个教学计划（使用 Session 验证）
    """
    # 从 session 中获取用户 ID
    teacher_id = session.get('user_id')
    if not teacher_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # 查询教学计划
    lesson_plan = LessonPlan.query.get(plan_id)
    if not lesson_plan:
        return jsonify({'message': 'Lesson plan not found'}), 404

    # 检查教学计划是否属于当前用户
    if lesson_plan.teacher_id != teacher_id:
        return jsonify({'message': 'Unauthorized'}), 403

    return jsonify({'lesson_plan': lesson_plan.to_dict()}), 200

@lesson_plan_bp.route('/<int:plan_id>', methods=['PUT'])
def update_lesson_plan(plan_id):
    """
    更新教学计划（使用 Session 验证）
    """
    # 从 session 中获取用户 ID
    teacher_id = session.get('user_id')
    if not teacher_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # 查询教学计划
    lesson_plan = LessonPlan.query.get(plan_id)
    if not lesson_plan:
        return jsonify({'message': 'Lesson plan not found'}), 404

    # 检查教学计划是否属于当前用户
    if lesson_plan.teacher_id != teacher_id:
        return jsonify({'message': 'Unauthorized'}), 403

    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    # 更新字段
    if data.get('title'):
        lesson_plan.title = data['title']
    if data.get('description'):
        lesson_plan.description = data['description']
    if data.get('content'):
        lesson_plan.content = data['content']
    if data.get('status'):
        lesson_plan.status = data['status']
    if data.get('generated_by'):
        lesson_plan.generated_by = data['generated_by']

    # 提交更改
    db.session.commit()

    return jsonify({
        'message': 'Lesson plan updated successfully',
        'plan': lesson_plan.to_dict()
    }), 200

@lesson_plan_bp.route('/<int:plan_id>', methods=['DELETE'])
def delete_lesson_plan(plan_id):
    """
    删除教学计划（使用 Session 验证）
    """
    # 从 session 中获取用户 ID
    teacher_id = session.get('user_id')
    if not teacher_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # 查询教学计划
    lesson_plan = LessonPlan.query.get(plan_id)
    if not lesson_plan:
        return jsonify({'message': 'Lesson plan not found'}), 404

    # 检查教学计划是否属于当前用户
    if lesson_plan.teacher_id != teacher_id:
        return jsonify({'message': 'Unauthorized'}), 403

    # 删除教学计划
    db.session.delete(lesson_plan)
    db.session.commit()

    return jsonify({'message': 'Lesson plan deleted successfully'}), 200

@lesson_plan_bp.route('/index')
def index():
    """
    渲染首页
    """
    return render_template('index.html')

@lesson_plan_bp.route('/lessonplan')
def lessonplan():
    return render_template('lessonplan.html')