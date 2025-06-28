from flask import Blueprint, session

from app.models.user import User

knowledge_for_teachers_bp=Blueprint('knowledge_for_teachers', __name__)

def is_logged_in():
    return 'user_id' in session

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

