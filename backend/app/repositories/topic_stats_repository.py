"""
Repository para consultas de métricas e estatísticas de tópicos.
Usado pelo sistema de priorização para decidir quais tópicos buscar.
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from sqlalchemy import select, func, and_
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from app.extensions import db
from app.entities.topic_entity import TopicEntity
from app.entities.user_topic_entity import UserTopicEntity
from app.entities.news_topic_entity import NewsTopicEntity
from app.entities.news_entity import NewsEntity


@dataclass
class TopicMetrics:
    """
    Representa as métricas de um tópico.

    Attributes:
        topic_id: ID do tópico
        topic_name: Nome do tópico
        user_count: Quantidade de usuários interessados neste tópico
        news_count_7d: Quantidade de notícias deste tópico nos últimos 7 dias
    """
    topic_id: int
    topic_name: str
    user_count: int
    news_count_7d: int

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "topic_id": self.topic_id,
            "topic_name": self.topic_name,
            "user_count": self.user_count,
            "news_count_7d": self.news_count_7d
        }


class TopicStatsRepository:
    """
    Repository para consultar estatísticas e métricas de tópicos.
    """

    def __init__(self, session=None):
        self.session = session or db.session

    def get_topic_metrics(self, days: int = 7) -> List[TopicMetrics]:
        """
        Retorna métricas de todos os tópicos.

        Consulta:
        - Quantidade de usuários interessados em cada tópico
        - Quantidade de notícias de cada tópico nos últimos N dias

        Args:
            days: Quantidade de dias para considerar nas notícias

        Returns:
            Lista de TopicMetrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Subquery para contar usuários por tópico
            users_subquery = (
                select(
                    UserTopicEntity.topic_id,
                    func.count(func.distinct(UserTopicEntity.user_id)).label('user_count')
                )
                .group_by(UserTopicEntity.topic_id)
                .subquery()
            )

            # Subquery para contar notícias recentes por tópico
            news_subquery = (
                select(
                    NewsTopicEntity.topic_id,
                    func.count(func.distinct(NewsEntity.id)).label('news_count')
                )
                .join(NewsEntity, NewsEntity.id == NewsTopicEntity.news_id)
                .where(NewsEntity.created_at > cutoff_date)
                .group_by(NewsTopicEntity.topic_id)
                .subquery()
            )

            # Query principal: juntar tópicos com suas métricas
            stmt = (
                select(
                    TopicEntity.id,
                    TopicEntity.name,
                    func.coalesce(users_subquery.c.user_count, 0).label('user_count'),
                    func.coalesce(news_subquery.c.news_count, 0).label('news_count_7d')
                )
                .outerjoin(users_subquery, TopicEntity.id == users_subquery.c.topic_id)
                .outerjoin(news_subquery, TopicEntity.id == news_subquery.c.topic_id)
                .order_by(func.coalesce(users_subquery.c.user_count, 0).desc())
            )

            results = self.session.execute(stmt).all()

            metrics = [
                TopicMetrics(
                    topic_id=row.id,
                    topic_name=row.name,
                    user_count=row.user_count,
                    news_count_7d=row.news_count_7d
                )
                for row in results
            ]

            logging.info(f"Métricas carregadas para {len(metrics)} tópicos")
            return metrics

        except SQLAlchemyError as e:
            logging.error(f"Erro ao buscar métricas de tópicos: {e}", exc_info=True)
            raise

    def get_topics_with_users(self) -> List[TopicMetrics]:
        """
        Retorna métricas apenas de tópicos que têm pelo menos 1 usuário interessado.

        Returns:
            Lista de TopicMetrics filtrada
        """
        all_metrics = self.get_topic_metrics()
        filtered = [m for m in all_metrics if m.user_count > 0]

        logging.info(f"{len(filtered)} tópicos têm usuários interessados")
        return filtered

    def get_user_count_for_topic(self, topic_id: int) -> int:
        """
        Retorna quantidade de usuários interessados em um tópico específico.

        Args:
            topic_id: ID do tópico

        Returns:
            Quantidade de usuários
        """
        try:
            stmt = (
                select(func.count(func.distinct(UserTopicEntity.user_id)))
                .where(UserTopicEntity.topic_id == topic_id)
            )
            result = self.session.execute(stmt).scalar()
            return result or 0

        except SQLAlchemyError as e:
            logging.error(f"Erro ao contar usuários do tópico {topic_id}: {e}", exc_info=True)
            return 0

    def get_news_count_for_topic(self, topic_id: int, days: int = 7) -> int:
        """
        Retorna quantidade de notícias de um tópico nos últimos N dias.

        Args:
            topic_id: ID do tópico
            days: Quantidade de dias

        Returns:
            Quantidade de notícias
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            stmt = (
                select(func.count(func.distinct(NewsEntity.id)))
                .join(NewsTopicEntity, NewsEntity.id == NewsTopicEntity.news_id)
                .where(
                    and_(
                        NewsTopicEntity.topic_id == topic_id,
                        NewsEntity.created_at > cutoff_date
                    )
                )
            )

            result = self.session.execute(stmt).scalar()
            return result or 0

        except SQLAlchemyError as e:
            logging.error(f"Erro ao contar notícias do tópico {topic_id}: {e}", exc_info=True)
            return 0

    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna um resumo geral das métricas do sistema.

        Returns:
            Dicionário com estatísticas gerais
        """
        metrics = self.get_topic_metrics()

        total_topics = len(metrics)
        topics_with_users = len([m for m in metrics if m.user_count > 0])
        topics_with_news = len([m for m in metrics if m.news_count_7d > 0])
        total_users = sum(m.user_count for m in metrics)
        total_news = sum(m.news_count_7d for m in metrics)

        return {
            "total_topics": total_topics,
            "topics_with_users": topics_with_users,
            "topics_with_news": topics_with_news,
            "total_user_interests": total_users,
            "total_news_7d": total_news
        }
