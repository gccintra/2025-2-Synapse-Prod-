import logging
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.entities.custom_topic_entity import CustomTopicEntity
from app.models.custom_topic import CustomTopic


class CustomTopicRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def create(self, model: CustomTopic) -> CustomTopic:
        try:
            entity = model.to_orm()
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return CustomTopic.from_entity(entity)
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao criar tópico customizado: {e}", exc_info=True)
            self.session.rollback()
            raise

    def find_by_name(self, name: str) -> CustomTopic | None:
        try:
            stmt = select(CustomTopicEntity).where(func.lower(CustomTopicEntity.name) == name.lower())
            entity = self.session.execute(stmt).scalar_one_or_none()
            return CustomTopic.from_entity(entity) if entity else None
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao buscar tópico customizado por nome: {e}", exc_info=True)
            raise

    def find_by_ids(self, topic_ids: list[int]) -> list[CustomTopic]:
        if not topic_ids:
            return []
        try:
            stmt = (
                select(CustomTopicEntity)
                .where(CustomTopicEntity.id.in_(topic_ids))
                .order_by(CustomTopicEntity.name)
            )
            entities = self.session.execute(stmt).scalars().all()
            return [CustomTopic.from_entity(e) for e in entities]
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao buscar tópicos customizados por IDs: {e}", exc_info=True)
            raise