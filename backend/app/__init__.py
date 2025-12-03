import os
from flask import Flask
from datetime import timedelta
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_swagger_ui import get_swaggerui_blueprint
from app.routes.user_routes import user_bp
from app.routes.topic_routes import topic_bp
from app.routes.news_source_routes import news_source_bp
from app.routes.news_routes import news_bp

def create_app(config_overrides=None):
    app = Flask(__name__)

    # --- CONFIGURAÇÃO DO CORS ---
    allowed_origins = ["http://localhost:5173"]
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        allowed_origins.append(frontend_url)

    CORS(app, origins=allowed_origins, supports_credentials=True)
    
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    # --- CORREÇÃO DATABASE URL ---
    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
    app.config["MAILTRAP_USER"]= os.getenv("MAILTRAP_USER")
    app.config["MAILTRAP_PASSWORD"]= os.getenv("MAILTRAP_PASSWORD")
    
    if config_overrides:
        app.config.update(config_overrides)

    SWAGGER_URL = '/api/docs' 
    API_URL = '/static/openapi.yaml'  

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL, API_URL,
        config={'app_name': "Synapse API Documentation"}
    )
    app.register_blueprint(swaggerui_blueprint)

    from app.extensions import db
    db.init_app(app)
    jwt = JWTManager(app)

    # Importa entidades para o SQLAlchemy saber que elas existem
    from app.entities import (custom_topic_entity, news_entity, news_source_entity, topic_entity, user_entity, user_preferred_custom_topics, user_preferred_news_sources_entity, user_saved_news_entity, user_read_history_entity)

    # --- REMOVIDO: db.create_all() e lógica de tópicos ---
    # Isso agora roda no init_db.py

    app.register_blueprint(user_bp, url_prefix="/users")
    app.register_blueprint(topic_bp, url_prefix="/topics")
    app.register_blueprint(news_bp, url_prefix="/news")
    app.register_blueprint(news_source_bp, url_prefix="/news_sources")

    return app