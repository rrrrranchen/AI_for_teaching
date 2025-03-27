from venv import logger
from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.question import Question
from app.models.course import Course
from app.services.demo import mock_ai_interface
from app.models.user import User
from app.models.courseclass import Courseclass
resource_bp=Blueprint('resource',__name__)