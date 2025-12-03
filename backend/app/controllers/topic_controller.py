import logging
from flask import request, jsonify
from app.services.user_custom_topic_service import UserCustomTopicService
from app.services.topic_service import TopicService
from app.models.exceptions import CustomTopicValidationError


class TopicController:
    def __init__(self):
        self.custom_topic_service = UserCustomTopicService()
        self.standard_topic_service = TopicService()

    def list_user_preferred_topics(self, user_id: int):
        try:
            topics = self.custom_topic_service.get_user_preferred_topics(user_id)
            statistics = self.custom_topic_service.get_user_statistics(user_id)

            return jsonify({
                "success": True,
                "message": "Tópicos customizados obtidos com sucesso.",
                "data": {"topics": topics, "statistics": statistics},
                "error": None
            }), 200

        except Exception as e:
            logging.error(f"Erro ao listar tópicos do usuário {user_id}: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "message": "Erro interno ao buscar tópicos.",
                "data": None, "error": str(e)
            }), 500

    def add_preferred_topic(self, user_id: int):
        try:
            data = request.get_json()
            if not data or 'name' not in data:
                return jsonify({
                    "success": False,
                    "message": "Campo 'name' é obrigatório.",
                    "data": None, "error": "Dados inválidos"
                }), 400

            name = data['name']
            result = self.custom_topic_service.add_preferred_topic(user_id, name)
            message = "Tópico adicionado com sucesso." if result["attached"] else "Tópico já estava em suas preferências."

            return jsonify({
                "success": True,
                "message": message,
                "data": result,
                "error": None
            }), 201

        except CustomTopicValidationError as e:
            return jsonify({
                "success": False,
                "message": "Dados inválidos.",
                "data": None, "error": str(e)
            }), 400

        except Exception as e:
            logging.error(f"Erro ao criar tópico para usuário {user_id}: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "message": "Erro interno ao criar tópico.",
                "data": None, "error": str(e)
            }), 500

    def remove_preferred_topic(self, user_id: int, topic_id: int):
        """
        Remove um tópico customizado das preferências do usuário.
        """
        try:
            success = self.custom_topic_service.remove_preferred_topic(user_id, topic_id)

            if not success:
                return jsonify({
                    "success": False,
                    "message": "Tópico não encontrado.",
                    "data": None, "error": "Not Found"
                }), 404

            return jsonify({
                "success": True,
                "message": "Tópico removido das preferências com sucesso.",
                "data": {"topic_id": topic_id},
                "error": None
            }), 200

        except Exception as e:
            logging.error(f"Erro ao deletar tópico {topic_id} do usuário {user_id}: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "message": "Erro interno ao remover tópico.",
                "data": None, "error": str(e)
            }), 500

    def get_statistics(self, user_id: int):
        try:
            statistics = self.custom_topic_service.get_user_statistics(user_id)

            return jsonify({
                "success": True,
                "message": "Estatísticas obtidas com sucesso.",
                "data": statistics,
                "error": None
            }), 200

        except Exception as e:
            logging.error(f"Erro ao buscar estatísticas do usuário {user_id}: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "message": "Erro interno ao buscar estatísticas.",
                "data": None, "error": str(e)
            }), 500

    # --- Métodos para Tópicos Padrão ---

    def list_standard_topics(self):
        try:
            topics = self.standard_topic_service.list_all_standard_topics()
            data = [{"id": t.id, "name": t.name, "state": t.state} for t in topics]
            return jsonify({
                "success": True,
                "message": "Tópicos padrão recuperados com sucesso.",
                "data": data,
                "error": None
            }), 200
        except Exception as e:
            logging.error(f"Erro inesperado ao listar tópicos padrão: {e}", exc_info=True)
            return jsonify({
                "success": False,
                "message": "Erro interno do servidor.",
                "data": None, "error": "Ocorreu um erro inesperado."
            }), 500
