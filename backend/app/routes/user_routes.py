from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, unset_access_cookies
from typing import Optional
from app.controllers.user_controller import UserController

user_bp = Blueprint("users", __name__)
user_controller = UserController()

def get_user_id_from_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = int(get_jwt_identity())
            return f(user_id, *args, **kwargs)
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Token inválido.",
                "data": None,
                "error": "A identidade do usuário no token é inválida ou está ausente."
            }), 400
    return decorated_function

def get_optional_user_id_from_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            identity = get_jwt_identity()
            user_id: Optional[int] = int(identity) if identity is not None else None
            return f(user_id, *args, **kwargs)
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Token inválido.",
                "data": None,
                "error": "A identidade do usuário no token é inválida."
            }), 400
    return decorated_function

@user_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    return user_controller.register(data)

@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    return user_controller.login(data)

@user_bp.route("/logout", methods=["POST"])
@jwt_required()
@get_user_id_from_token
def logout(user_id: int):
    return user_controller.logout(user_id)

@user_bp.route("/profile", methods=["GET"])
@jwt_required()
@get_user_id_from_token
def get_profile(user_id: int):
    return user_controller.get_profile(user_id)

@user_bp.route("/profile/update", methods=["PUT"])
@jwt_required()
@get_user_id_from_token
def update_profile(user_id: int):
    data = request.get_json()
    return user_controller.update_profile(user_id, data)

@user_bp.route("/profile/change_password", methods=["PUT"])
@jwt_required()
@get_user_id_from_token
def update_my_password(user_id: int):
    data = request.get_json()
    return user_controller.update_password(user_id, data)

@user_bp.route("/login/google", methods=["POST"])
def google_login():
    data = request.get_json()
    return user_controller.google_login(data)