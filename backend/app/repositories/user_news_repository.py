from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.extensions import db
from app.entities.user_news_entity import UserNewsEntity
from app.models.user_news import UserNews

class UserNewsRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def set_favorite(self, user_id: int, news_id: int, is_favorite: bool = True) -> UserNews:
        try:
            stmt = select(UserNewsEntity).where(
                UserNewsEntity.user_id == user_id,
                UserNewsEntity.news_id == news_id
            )

            entity = self.session.execute(stmt).scalar_one_or_none()

            if entity:
                entity.is_favorite = is_favorite
                updated_entity = self.session.merge(entity)
            else:
                new_entity = UserNewsEntity(user_id=user_id, news_id=news_id, is_favorite=is_favorite)
                self.session.add(new_entity)
                updated_entity = new_entity

            self.session.commit()
            self.session.refresh(updated_entity)

            return UserNews(
                id=updated_entity.id,
                user_id=updated_entity.user_id,
                news_id=updated_entity.news_id,
                is_favorite=updated_entity.is_favorite
            )
        except SQLAlchemyError as e:
            logging.error(f"Erro ao definir favorito user_id={user_id}, news_id={news_id}: {e}", exc_info=True)
            self.session.rollback()
            raise

    def get_favorites_by_user(self, user_id: int) -> list[UserNews]:
        try:
            stmt = select(UserNewsEntity).where(
                UserNewsEntity.user_id == user_id,
                UserNewsEntity.is_favorite == True
            )
            entities = self.session.execute(stmt).scalars().all()
            return [
                UserNews(
                    id=e.id,
                    user_id=e.user_id,
                    news_id=e.news_id,
                    is_favorite=e.is_favorite
                )
                for e in entities
            ]
        except SQLAlchemyError as e:
            logging.error(f"Erro ao buscar favoritos para user_id={user_id}: {e}", exc_info=True)
            raise
