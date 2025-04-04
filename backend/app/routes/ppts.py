from flask import Blueprint, render_template, request, jsonify, session
from sqlalchemy import func, select
from app.utils.database import db
from app.models.course import Course
from app.models.courseclass import Courseclass
from app.models.user import User
from app.models.relationship import teacher_class
from app.models.relationship import student_class

ppts_bp = Blueprint('ppts', __name__)

