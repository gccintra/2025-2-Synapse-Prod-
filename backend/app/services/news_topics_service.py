from app.repositories.news_topic_repository import NewsTopicRepository
from app.models.news import News
import logging
import math

class NewsTopicsService:
    def __init__(self, news_topic_repo: NewsTopicRepository | None = None):
        self.news_topic_repo = news_topic_repo or NewsTopicRepository()

    def find_by_topic(self, topic_id: int, page: int = 1, per_page: int = 10) -> dict:
        try:
            # Buscar notícias paginadas
            entities = self.news_topic_repo.find_news_by_topic(topic_id, page, per_page)

            # Contar total de notícias para o tópico
            total_count = self.news_topic_repo.count_by_topic(topic_id)

            # Converter entidades para modelos News e depois para dicionários
            news_list = []
            for entity in entities:
                news = News.from_entity(entity)
                news_dict = {
                    "id": news.id,
                    "title": news.title,
                    "description": news.description,
                    "url": news.url,
                    "image_url": news.image_url,
                    "content": news.content,
                    "published_at": news.published_at.isoformat() if news.published_at else None,
                    "source_id": news.source_id,
                    "created_at": news.created_at.isoformat() if news.created_at else None,
                }

                # Incluir nome da fonte se disponível
                if news.source_name:
                    news_dict["source_name"] = news.source_name

                news_list.append(news_dict)

            # Calcular total de páginas
            total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

            return {
                "news": news_list,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total_count,
                    "pages": total_pages
                }
            }
        except Exception as e:
            logging.error(f"Erro no service ao buscar notícias por tópico: {e}", exc_info=True)
            raise
