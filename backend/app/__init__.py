# app.py
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from app.routes.lesson_plan import lesson_plan_bp
from app.routes.auth import auth_bp
from app.utils.database import init_db

from app.utils.database import db

def create_app():
    app = Flask(__name__)

    
   
    init_db(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(lesson_plan_bp)
    app.secret_key='sadfasdfgghgafdshg'
    return app