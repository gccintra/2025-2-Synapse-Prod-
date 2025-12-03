import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, literal, case, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.entities.news_entity import NewsEntity
from app.entities.news_source_entity import NewsSourceEntity
from app.entities.user_saved_news_entity import UserSavedNewsEntity
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
            return stmt.add_columns(literal(False).label("is_favorite"))

        favorite_subquery = (
            select(literal(True))
            .where(
                UserSavedNewsEntity.user_id == user_id,
                UserSavedNewsEntity.news_id == NewsEntity.id,
                UserSavedNewsEntity.is_favorite == True,
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

    def _normalize_url(self, url: str) -> str:
        if not url:
            return url

        try:
            from urllib.parse import urlparse, urlunparse

            parsed = urlparse(url.lower().strip())

            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc.replace('www.', ''),  # Remove www
                parsed.path.rstrip('/'),            # Remove trailing slash
                '',  # params
                '',  # query - remove query parameters
                ''   # fragment
            ))

            return normalized

        except Exception as e:
            logging.warning(f"Erro ao normalizar URL '{url}': {e}")
            return url.lower().strip()

    def find_by_url(self, url: str) -> News | None:
        try:
            # Tentar busca exata primeiro (para compatibilidade)
            stmt = select(NewsEntity).where(NewsEntity.url == url)
            entity = self.session.execute(stmt).scalar_one_or_none()

            if entity:
                return News.from_entity(entity)

            # Se não encontrou, tentar com URL normalizada
            normalized_url = self._normalize_url(url)
            if normalized_url != url:
                stmt = select(NewsEntity).where(NewsEntity.url == normalized_url)
                entity = self.session.execute(stmt).scalar_one_or_none()

                if entity:
                    return News.from_entity(entity)

                stmt = select(NewsEntity)
                entities = self.session.execute(stmt).scalars().all()

                for existing_entity in entities:
                    if self._normalize_url(existing_entity.url) == normalized_url:
                        return News.from_entity(existing_entity)

            return None

        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao buscar notícia por URL: {e}", exc_info=True)
            raise

    def find_by_title(self, title: str) -> News | None:
        """Busca uma notícia pelo título (case-insensitive)."""
        try:
            stmt = select(NewsEntity).where(func.lower(NewsEntity.title) == title.lower())
            entity = self.session.execute(stmt).scalar_one_or_none()
            return News.from_entity(entity) if entity else None
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao buscar notícia por título: {e}", exc_info=True)
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
                .join(NewsEntity.source)
                .options(joinedload(NewsEntity.source))
                .order_by(NewsEntity.published_at.desc(), NewsEntity.id.desc())
            )
            enriched_stmt = self._enrich_with_favorite_status(stmt, user_id)
            paginated_stmt = enriched_stmt.offset((page - 1) * per_page).limit(per_page)
            results = self.session.execute(paginated_stmt).all()
            return [self._map_result_to_model(row) for row in results]
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao listar notícias: {e}", exc_info=True)
            raise

    def find_by_topic(self, topic_id: int, page: int = 1, per_page: int = 10, user_id: Optional[int] = None) -> list[News]:
        """Busca notícias paginadas por um ID de tópico específico."""
        try:
            stmt = (
                select(NewsEntity)
                .where(NewsEntity.topic_id == topic_id)
                .options(joinedload(NewsEntity.source))
                .order_by(NewsEntity.published_at.desc(), NewsEntity.id.desc())
            )
            enriched_stmt = self._enrich_with_favorite_status(stmt, user_id)
            paginated_stmt = enriched_stmt.offset((page - 1) * per_page).limit(per_page)
            
            results = self.session.execute(paginated_stmt).all()
            return [self._map_result_to_model(row) for row in results]
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao buscar notícias por tópico: {e}", exc_info=True)
            raise

    def count_by_topic(self, topic_id: int) -> int:
        """Conta o total de notícias de um tópico específico."""
        try:
            stmt = (
                select(func.count(NewsEntity.id))
                .where(NewsEntity.topic_id == topic_id)
            )
            result = self.session.execute(stmt).scalar()
            return result or 0
        except SQLAlchemyError as e:
            logging.error(f"Erro ao contar notícias por tópico: {e}", exc_info=True)
            raise

    def list_favorites_by_user(self, user_id: int, page: int = 1, per_page: int = 20) -> list[News]:
        try:
            stmt = (
                select(NewsEntity)
                .join(UserSavedNewsEntity, NewsEntity.id == UserSavedNewsEntity.news_id)
                .where(UserSavedNewsEntity.user_id == user_id)
                .where(UserSavedNewsEntity.is_favorite == True)
                .options(joinedload(NewsEntity.source))
                .order_by(NewsEntity.published_at.desc(), NewsEntity.id.desc())
            )
            paginated_stmt = stmt.offset((page - 1) * per_page).limit(per_page)
            results = self.session.execute(paginated_stmt).scalars().all()
            return [News.from_entity(row) for row in results]
        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao listar notícias favoritas: {e}", exc_info=True)
            raise

    def get_recent_news_with_base_score(self, user_id: int, preferred_source_ids: list[int], days_limit: int = 15) -> list[News]:
        """
        Busca notícias dos últimos X dias com scores pré-calculados.

        Calcula no banco:
        - Score temporal baseado na data de publicação
        - Score de fonte preferida baseado nas preferências do usuário

        Args:
            user_id: ID do usuário para status de favorited
            preferred_source_ids: Lista de IDs das fontes preferidas
            days_limit: Número de dias para filtrar (padrão: 15)

        Returns:
            Lista de notícias com campos time_score e source_score
        """
        try:
            # Data limite para filtrar notícias
            cutoff_date = datetime.now() - timedelta(days=days_limit)

            # Score temporal usando CASE WHEN
            time_score_case = case(
                (NewsEntity.published_at >= datetime.now() - timedelta(days=1), 300),  # Últimas 24h
                (NewsEntity.published_at >= datetime.now() - timedelta(days=2), 150),  # 1-2 dias
                (NewsEntity.published_at >= datetime.now() - timedelta(days=5), 75),   # 2-5 dias
                else_=25  # 5+ dias
            ).label("time_score")

            # Score de fonte preferida usando CASE WHEN
            source_score_case = case(
                (NewsEntity.source_id.in_(preferred_source_ids) if preferred_source_ids else False, 100),
                else_=0
            ).label("source_score")

            # Query principal com joins e scores
            stmt = (
                select(NewsEntity, time_score_case, source_score_case)
                .join(NewsEntity.source)
                .options(joinedload(NewsEntity.source))
                .where(NewsEntity.published_at >= cutoff_date)
                .order_by(NewsEntity.published_at.desc())
            )

            # Adicionar status de favorited
            enriched_stmt = self._enrich_with_favorite_status_for_scoring(stmt, user_id)

            results = self.session.execute(enriched_stmt).all()
            return [self._map_scoring_result_to_model(row) for row in results]

        except SQLAlchemyError as e:
            logging.error(f"Erro de banco ao buscar notícias com score base: {e}", exc_info=True)
            raise

    def _enrich_with_favorite_status_for_scoring(self, stmt, user_id: Optional[int]):
        """Versão especializada do _enrich_with_favorite_status para queries com scores."""
        if user_id is None:
            return stmt.add_columns(literal(False).label("is_favorited"))

        favorite_subquery = (
            select(literal(True))
            .where(
                UserSavedNewsEntity.user_id == user_id,
                UserSavedNewsEntity.news_id == NewsEntity.id,
                UserSavedNewsEntity.is_favorite == True,
            )
            .exists()
        ).label("is_favorited")

        return stmt.add_columns(favorite_subquery)

    def _map_scoring_result_to_model(self, result_row) -> News:
        """Mapeia resultado com scores (entidade, time_score, source_score, is_favorited) para o modelo."""
        news_entity, time_score, source_score, is_favorited = result_row
        news_model = News.from_entity(news_entity)
        news_model.is_favorited = is_favorited or False

        # Adicionar scores como atributos temporários
        news_model.time_score = time_score
        news_model.source_score = source_score

        return news_model