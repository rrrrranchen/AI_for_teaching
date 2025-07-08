import os
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from .utils.database import init_db
from app.routes.auth import auth_bp
from app.routes.courseclass import courseclass_bp
from app.routes.course import course_bp
from app.routes.question import question_bp
from app.routes.student_answer import student_answer_bp
from app.routes.resource import resource_bp
from app.routes.forum import forum_bp
from app.routes.teaching_design import teaching_design_bp
from app.routes.teacher_recommend import teacher_recommend_bp
from app.routes.student_recommend import student_recommend_bp
from app.routes.human_management import human_management_bp
from app.routes.mindmap import mindmap_bp
from app.routes.courseclass_management import courseclass_management_bp
from app.routes.ppt_templates_management import ppt_templates_management_bp
from app.routes.dashBoard import dashboard_bp
from app.routes.knowledge_for_teachers import knowledge_for_teachers_bp
from app.routes.knowledge_management import knowledge_management_bp
from app.utils.database import init_db
from app.config import Config
from flask_jwt_extended import JWTManager
from app.routes.ai_chat import ai_chat_bp
# 初始化 Flask 应用
def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static')
    app.config.from_object(Config)
    print("ALLOWED_EXTENSIONS:", app.config.get('ALLOWED_EXTENSIONS', set()))
    app.config["JWT_SECRET_KEY"] = "sadfasdfgghgafdshg"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600
    app.secret_key = "jskldjflksdjlfksjd"
    # 初始化数据库
    init_db(app)
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(courseclass_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(question_bp)
    app.register_blueprint(student_answer_bp)
    app.register_blueprint(resource_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(teaching_design_bp)
    app.register_blueprint(teacher_recommend_bp)
    app.register_blueprint(student_recommend_bp)
    app.register_blueprint(mindmap_bp)
    app.register_blueprint(human_management_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(courseclass_management_bp)
    app.register_blueprint(ppt_templates_management_bp)
    app.register_blueprint(knowledge_for_teachers_bp)
    app.register_blueprint(ai_chat_bp)
    app.register_blueprint(knowledge_management_bp)
    return app
