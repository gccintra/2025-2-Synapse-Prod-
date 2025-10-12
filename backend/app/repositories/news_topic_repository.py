import logging
from app.extensions import db
from sqlalchemy import select, join
from app.entities.news_entity import NewsEntity
from app.entities.news_topic_entity import NewsTopicEntity
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
class NewsTopicRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def create_association(self, news_id: int, topic_id: int) -> NewsTopicEntity:
        try:
            entity = NewsTopicEntity(news_id=news_id, topic_id=topic_id)
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity
        except IntegrityError as e:
            logging.debug(f"Associação news_id={news_id}, topic_id={topic_id} já existe.")
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao criar associação news-topic: {e}", exc_info=True)
            self.session.rollback()
            raise

    def find_news_by_topic(self, topic_id: int, page: int = 1, per_page: int = 10) -> list[NewsEntity]:
        try:
            j = join(NewsTopicEntity, NewsEntity, NewsTopicEntity.news_id == NewsEntity.id)
            stmt = (
                select(NewsEntity)
                .select_from(j)
                .where(NewsTopicEntity.topic_id == topic_id)
                .order_by(NewsEntity.published_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            result = self.session.execute(stmt).scalars().all()
            return result
        except SQLAlchemyError as e:
            logging.error(f"Erro ao buscar notícias por tópico no NewsTopicRepository: {e}", exc_info=True)
            raise
