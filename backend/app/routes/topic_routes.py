from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.controllers.topic_controller import TopicController

topic_bp = Blueprint("topics", __name__)
topic_controller = TopicController()

def _get_user_id_from_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            user_id = int(get_jwt_identity())
            return f(user_id, *args, **kwargs)
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Token inválido.", "data": None, "error": "Identidade inválida."}), 400
    return decorated

# --- Rotas para Tópicos Padrão (Públicas ou semi-públicas) ---

@topic_bp.route("/standard", methods=["GET"])
def list_standard_topics():
    """Lista todos os tópicos padrão do sistema."""
    return topic_controller.list_standard_topics()

# --- Rotas para Tópicos Customizados (Preferências do Usuário) ---

@topic_bp.route("/custom", methods=["GET"])
@jwt_required()
@_get_user_id_from_token
def list_user_preferred_topics(user_id: int):
    """Lista os tópicos customizados preferidos do usuário."""
    return topic_controller.list_user_preferred_topics(user_id)

@topic_bp.route("/custom", methods=["POST"])
@jwt_required()
@_get_user_id_from_token
def add_preferred_topic(user_id: int):
    """Adiciona um tópico customizado às preferências do usuário."""
    return topic_controller.add_preferred_topic(user_id)

@topic_bp.route("/custom/<int:topic_id>", methods=["DELETE"])
@jwt_required()
@_get_user_id_from_token
def remove_preferred_topic(user_id: int, topic_id: int):
    """Remove um tópico customizado das preferências do usuário."""
    return topic_controller.remove_preferred_topic(user_id, topic_id)

@topic_bp.route("/custom/statistics", methods=["GET"])
@jwt_required()
@_get_user_id_from_token
def get_statistics(user_id: int):
    """Retorna estatísticas dos tópicos customizados do usuário."""
    return topic_controller.get_statistics(user_id)