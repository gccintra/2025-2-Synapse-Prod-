from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, unset_access_cookies
from app.controllers.news_controller import NewsController
from app.routes.user_routes import get_user_id_from_token 

news_bp = Blueprint("news", __name__)
news_controller = NewsController()

@news_bp.route("/<int:news_id>/favorite", methods=["POST"])
@jwt_required()
@get_user_id_from_token
def favorite_news(user_id, news_id):
    return news_controller.favorite_news(user_id, news_id)

@news_bp.route("/<int:news_id>/unfavorite", methods=["DELETE"])
@jwt_required()
@get_user_id_from_token
def unfavorite_news(user_id, news_id):
    return news_controller.unfavorite_news(user_id, news_id)

