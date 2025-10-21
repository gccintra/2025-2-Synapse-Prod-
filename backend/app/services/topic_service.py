from app.models.topic import Topic
from app.repositories.topic_repository import TopicRepository

class TopicService:
    """
    Serviço responsável pela lógica de negócio dos Tópicos Padrão.
    Tópicos padrão são definidos pelo sistema e não podem ser criados por usuários.
    """
    def __init__(self, topic_repo: TopicRepository | None = None):
        self.topic_repo = topic_repo or TopicRepository()

    def list_all_standard_topics(self) -> list[Topic]:
        """Lista todos os tópicos padrão ativos no sistema."""
        return self.topic_repo.list_all()
