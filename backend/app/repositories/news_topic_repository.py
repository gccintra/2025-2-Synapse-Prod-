import logging
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.extensions import db
from app.entities.news_topic_entity import NewsTopicEntity


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
