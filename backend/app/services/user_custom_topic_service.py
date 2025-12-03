import logging
from typing import Optional
from sqlalchemy.exc import IntegrityError
from app.repositories.user_preferred_custom_topic_repository import UserPreferredCustomTopicRepository
from app.repositories.custom_topic_repository import CustomTopicRepository
from app.models.custom_topic import CustomTopic, CustomTopicValidationError


class UserCustomTopicService:
    MAX_TOPICS_PER_USER = 20

    def __init__(self,
                 custom_topic_repo: CustomTopicRepository | None = None,
                 preferred_repo: UserPreferredCustomTopicRepository | None = None):
        self.custom_topic_repo = custom_topic_repo or CustomTopicRepository()
        self.preferred_repo = preferred_repo or UserPreferredCustomTopicRepository() # Repositório para a tabela de associação

    def add_preferred_topic(self, user_id: int, name: str) -> dict:
        try:
            current_count = self.preferred_repo.count_by_user(user_id)
            if current_count >= self.MAX_TOPICS_PER_USER:
                raise CustomTopicValidationError("limit", f"Limite máximo de {self.MAX_TOPICS_PER_USER} tópicos atingido.")

            topic_model = CustomTopic(name=name) 

            topic = self.custom_topic_repo.find_by_name(topic_model.name)
            if not topic:
                try:
                    topic = self.custom_topic_repo.create(topic_model)
                except IntegrityError: 
                    logging.warning(f"Race condition ao criar tópico customizado '{topic_model.name}'. Buscando novamente.")
                    topic = self.custom_topic_repo.find_by_name(topic_model.name)
                    if not topic:
                        raise 

            attached = self.preferred_repo.attach(user_id, topic.id)

            if attached:
                logging.info(f"Tópico customizado '{topic.name}' associado ao usuário {user_id}.")
            else:
                logging.info(f"Tópico customizado '{topic.name}' já estava associado ao usuário {user_id}.")

            return {"topic": topic.to_dict(), "attached": attached}

        except CustomTopicValidationError:
            raise  
        except IntegrityError:
            raise
        except Exception as e: # Captura outras exceções inesperadas
            logging.error(f"Erro ao criar tópico customizado: {e}", exc_info=True)
            raise Exception("Erro interno ao adicionar tópico preferido.")

    def get_user_preferred_topics(self, user_id: int) -> list[dict]:
        try:
            topic_ids = self.preferred_repo.list_user_topic_ids(user_id)
            topics = self.custom_topic_repo.find_by_ids(topic_ids)
            return [topic.to_dict() for topic in topics]
        except Exception as e:
            logging.error(f"Erro ao buscar tópicos do usuário {user_id}: {e}", exc_info=True)
            return []

    def remove_preferred_topic(self, user_id: int, topic_id: int) -> bool:
        try:
            success = self.preferred_repo.detach(user_id, topic_id)

            if success:
                logging.info(f"Tópico customizado {topic_id} desassociado do usuário {user_id}")
            else:
                logging.warning(f"Associação do tópico {topic_id} não encontrada para o usuário {user_id}")

            return success

        except Exception as e:
            logging.error(f"Erro ao desassociar tópico {topic_id}: {e}", exc_info=True)
            return False

    def get_user_statistics(self, user_id: int) -> dict:
        try:
            current_count = self.preferred_repo.count_by_user(user_id)

            return {
                "total_topics": current_count,
                "max_allowed": self.MAX_TOPICS_PER_USER,
                "remaining": max(0, self.MAX_TOPICS_PER_USER - current_count),
                "can_create_more": current_count < self.MAX_TOPICS_PER_USER
            }

        except Exception as e:
            logging.error(f"Erro ao buscar estatísticas do usuário {user_id}: {e}", exc_info=True)
            return {
                "total_topics": 0,
                "max_allowed": self.MAX_TOPICS_PER_USER,
                "remaining": self.MAX_TOPICS_PER_USER,
                "can_create_more": True
            }