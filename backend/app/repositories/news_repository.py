import logging
from sqlalchemy import select, func, literal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.entities.news_entity import NewsEntity
from app.entities.news_source_entity import NewsSourceEntity
from app.entities.user_news_entity import UserNewsEntity
from app.models.news import News
from typing import Optional

class NewsRepository:
    def __init__(self, session=None):
        self.session = session or db.session

    def create(self, model: News) -> News:
        try:
            entity = model.to_orm()
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return News.from_entity(entity)
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao criar notícia: {e}", exc_info=True)
            self.session.rollback()
            raise

    def _enrich_with_favorite_status(self, stmt, user_id: Optional[int]):
        """Adiciona uma subconsulta para verificar o status de favorito."""
        if user_id is None:
            return stmt.add_columns(literal(False).label("is_favorited"))

        favorite_subquery = (
            select(literal(True))
            .where(
                UserNewsEntity.user_id == user_id,
                UserNewsEntity.news_id == NewsEntity.id,
                UserNewsEntity.is_favorite == True,
            )
            .exists()
        ).label("is_favorited")

        return stmt.add_columns(favorite_subquery)

    def _map_result_to_model(self, result_row) -> News:
        """Mapeia uma linha do resultado (entidade, is_favorited) para o modelo."""
        news_entity, is_favorited = result_row
        news_model = News.from_entity(news_entity)
        news_model.is_favorited = is_favorited or False
        return news_model

    def find_by_id(self, news_id: int, user_id: Optional[int] = None) -> News | None:
        try:
            stmt = select(NewsEntity).where(NewsEntity.id == news_id)
            enriched_stmt = self._enrich_with_favorite_status(stmt, user_id)
            result = self.session.execute(enriched_stmt).first()
            return self._map_result_to_model(result) if result else None
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao buscar notícia por ID: {e}", exc_info=True)
            raise

    def find_by_url(self, url: str) -> News | None:
        try:
            stmt = select(NewsEntity).where(NewsEntity.url == url)
            entity = self.session.execute(stmt).scalar_one_or_none()
            return News.from_entity(entity) if entity else None
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao buscar notícia por URL: {e}", exc_info=True)
            raise

    def count_all(self) -> int:
        """Conta o total de notícias no banco de dados."""
        try:
            stmt = select(func.count(NewsEntity.id))
            result = self.session.execute(stmt).scalar()
            return result or 0
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao contar notícias: {e}", exc_info=True)
            raise

    def list_all(self, page: int = 1, per_page: int = 20, user_id: Optional[int] = None) -> list[News]:
        try:
            stmt = (
                select(NewsEntity)
                .options(joinedload(NewsEntity.source))  # Carregar fonte junto
                .order_by(NewsEntity.published_at.desc())
            )
            enriched_stmt = self._enrich_with_favorite_status(stmt, user_id)
            paginated_stmt = enriched_stmt.offset((page - 1) * per_page).limit(per_page)
            results = self.session.execute(paginated_stmt).all()
            return [self._map_result_to_model(row) for row in results]
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao listar notícias: {e}", exc_info=True)
            raise

    def find_by_topic(self, news_id: int, topic_id: int) -> list[NewsEntity]:
        try:
            stmt = (
                select(NewsEntity)
                .where(NewsEntity.id == news_id)
                .where(NewsEntity.topic_id == topic_id)
            )
            entities = self.session.execute(stmt).scalars().all()
            return entities
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao buscar notícias por tópico: {e}", exc_info=True)
            raise