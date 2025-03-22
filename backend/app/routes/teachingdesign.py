from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.security import check_password_hash
from app.utils.database import db
from app.models.teachingdesign import TeachingDesign

teachingdesign_bp=Blueprint('teachingdesign',__name__)


def is_logged_in():
    return 'user_id' in session

