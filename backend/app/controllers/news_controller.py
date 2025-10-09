from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
import logging
from app.services.news_service import NewsService
from flask_jwt_extended import set_access_cookies, create_access_token, unset_jwt_cookies
from app.models.exceptions import UserNotFoundError, EmailInUseError

class NewsController:
    def __init__(self):
        self.service = NewsService()

    def favorite_news(self, user_id, news_id):
        try:
            print(user_id,news_id)
            fav = self.service.favorite_news(user_id, news_id)
            return jsonify({"success": True, "message": "Notícia favoritada.", "data": {"news_id": news_id}, "error": None}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "Erro ao favoritar notícia.", "data": None, "error": str(e)}), 500

    def unfavorite_news(self, user_id, news_id):
        try:
            fav = self.service.unfavorite_news(user_id, news_id)
            return jsonify({"success": True, "message": "Notícia removida dos favoritos.", "data": {"news_id": news_id}, "error": None}), 200
        except Exception as e:
            return jsonify({"success": False, "message": "Erro ao remover favorito.", "data": None, "error": str(e)}), 500