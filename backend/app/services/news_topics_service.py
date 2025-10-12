from app.repositories.news_topic_repository import NewsTopicRepository
from app.models.news import News
import logging

class NewsTopicsService:
    def __init__(self, news_topic_repo: NewsTopicRepository | None = None):
        self.news_topic_repo = news_topic_repo or NewsTopicRepository()

    def find_by_topic(self, topic_id: int, page: int = 1, per_page: int = 10) -> list[dict]:
        try:
            entities = self.news_topic_repo.find_news_by_topic(topic_id, page, per_page)
            return [
                {
                    "id": news.id,
                    "title": news.title,
                    "image_url": news.image_url,
                    "description": news.description,
                    "published_at": news.published_at.isoformat() if news.published_at else None,
                }
                for news in entities
            ]
        except Exception as e:
            logging.error(f"Erro no service ao buscar notícias por tópico: {e}", exc_info=True)
            raise
