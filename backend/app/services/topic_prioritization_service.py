"""
Serviço de priorização de tópicos para coleta inteligente de notícias.
Calcula scores baseado em interesse de usuários, cobertura de notícias e cache.
"""

import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
from app.repositories.topic_stats_repository import TopicStatsRepository, TopicMetrics
from app.utils.topic_search_cache import TopicSearchCache
from app.config.news_collection_config import get_config


@dataclass
class TopicScore:
    """
    Representa um tópico com seu score de prioridade.

    Attributes:
        topic_id: ID do tópico
        topic_name: Nome do tópico
        score: Score calculado (quanto maior, mais prioritário)
        user_count: Quantidade de usuários interessados
        news_count_7d: Quantidade de notícias nos últimos 7 dias
        searches_6h: Quantidade de buscas nas últimas 6 horas
        is_blocked: Se o tópico está bloqueado por excesso de buscas
    """
    topic_id: int
    topic_name: str
    score: float
    user_count: int
    news_count_7d: int
    searches_6h: int
    is_blocked: bool

    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            "topic_id": self.topic_id,
            "topic_name": self.topic_name,
            "score": self.score,
            "user_count": self.user_count,
            "news_count_7d": self.news_count_7d,
            "searches_6h": self.searches_6h,
            "is_blocked": self.is_blocked
        }


class TopicPrioritizationService:
    """
    Serviço responsável por priorizar tópicos para coleta de notícias.

    O algoritmo de priorização considera:
    1. Demanda: quantidade de usuários interessados no tópico
    2. Oferta: quantidade de notícias já coletadas recentemente
    3. Diversidade: bônus para tópicos não buscados recentemente
    4. Cache: penalidade para tópicos buscados repetidamente
    """

    def __init__(
        self,
        stats_repo: TopicStatsRepository = None,
        cache: TopicSearchCache = None,
        config: Dict = None
    ):
        """
        Inicializa o serviço de priorização.

        Args:
            stats_repo: Repository de estatísticas (se None, cria um novo)
            cache: Cache de buscas (se None, cria um novo)
            config: Configurações (se None, usa padrão)
        """
        self.stats_repo = stats_repo or TopicStatsRepository()
        self.cache = cache
        self.config = config or get_config()

        logging.info("TopicPrioritizationService inicializado")

    def get_prioritized_topics(
        self,
        count: int = None,
        min_users: int = 0
    ) -> List[TopicScore]:
        """
        Retorna lista de tópicos priorizados por score.

        Args:
            count: Quantidade de tópicos a retornar (se None, usa config)
            min_users: Mínimo de usuários para considerar o tópico

        Returns:
            Lista de TopicScore ordenada por score (maior primeiro)
        """
        if count is None:
            count = self.config["topics_to_select"]

        # Carregar métricas do banco
        all_metrics = self.stats_repo.get_topic_metrics(days=7)

        if not all_metrics:
            logging.warning("Nenhuma métrica de tópico encontrada no banco")
            return []

        # Filtrar tópicos com usuários suficientes
        filtered_metrics = [m for m in all_metrics if m.user_count >= min_users]

        if not filtered_metrics:
            logging.warning(
                f"Nenhum tópico com pelo menos {min_users} usuários. "
                f"Usando tópicos default."
            )
            return self._get_default_topic_scores(count)

        # Calcular scores
        topic_scores = self._calculate_scores(filtered_metrics)

        # Ordenar por score (maior primeiro) e pegar top N
        topic_scores.sort(key=lambda x: x.score, reverse=True)

        # Filtrar bloqueados
        available_topics = [t for t in topic_scores if not t.is_blocked]

        if len(available_topics) < count:
            logging.warning(
                f"Apenas {len(available_topics)} tópicos disponíveis "
                f"(requisitado: {count}). Usando tópicos default para complementar."
            )
            # Complementar com tópicos default se necessário
            default_scores = self._get_default_topic_scores(count - len(available_topics))
            available_topics.extend(default_scores)

        selected = available_topics[:count]

        logging.info(
            f"Selecionados {len(selected)} tópicos prioritários: "
            f"{[t.topic_name for t in selected]}"
        )

        return selected

    def _calculate_scores(self, metrics_list: List[TopicMetrics]) -> List[TopicScore]:
        """
        Calcula score de prioridade para cada tópico.

        Fórmula:
        score = (user_count × weight_user) - (news_count × weight_news)
                + diversity_bonus - cache_penalty

        Args:
            metrics_list: Lista de métricas de tópicos

        Returns:
            Lista de TopicScore
        """
        config = self.config
        scores = []

        for metrics in metrics_list:
            # Contar buscas no cache (se cache disponível)
            searches_6h = 0
            if self.cache:
                searches_6h = self.cache.count_searches_in_period(
                    metrics.topic_name,
                    hours=config["cache_ttl_hours"]
                )

            # Verificar se está bloqueado
            is_blocked = searches_6h >= config["max_searches_per_topic_in_6h"]

            # Calcular score base
            base_score = (
                metrics.user_count * config["score_user_weight"]
                - metrics.news_count_7d * config["score_news_weight"]
            )

            # Bônus de diversidade (se nunca foi buscado no período)
            diversity_bonus = config["score_diversity_bonus"] if searches_6h == 0 else 0

            # Penalidade de cache
            cache_penalty = searches_6h * config["score_cache_penalty"]

            # Score final (se bloqueado, score muito negativo)
            if is_blocked:
                final_score = -999999
            else:
                final_score = base_score + diversity_bonus - cache_penalty

            topic_score = TopicScore(
                topic_id=metrics.topic_id,
                topic_name=metrics.topic_name,
                score=final_score,
                user_count=metrics.user_count,
                news_count_7d=metrics.news_count_7d,
                searches_6h=searches_6h,
                is_blocked=is_blocked
            )

            scores.append(topic_score)

            logging.debug(
                f"Score calculado para '{metrics.topic_name}': {final_score:.1f} "
                f"(users={metrics.user_count}, news={metrics.news_count_7d}, "
                f"searches={searches_6h}, blocked={is_blocked})"
            )

        return scores

    def _get_default_topic_scores(self, count: int) -> List[TopicScore]:
        """
        Retorna scores de tópicos default quando não há dados suficientes.

        Args:
            count: Quantidade de tópicos

        Returns:
            Lista de TopicScore com tópicos default
        """
        default_topics = self.config["default_topics"][:count]

        default_scores = []
        for i, topic_name in enumerate(default_topics):
            # Score decrescente para manter ordem dos defaults
            base_score = 500 - (i * 10)

            # Ajustar por cache se disponível
            searches_6h = 0
            if self.cache:
                searches_6h = self.cache.count_searches_in_period(
                    topic_name,
                    hours=self.config["cache_ttl_hours"]
                )

            is_blocked = searches_6h >= self.config["max_searches_per_topic_in_6h"]

            if is_blocked:
                continue  # Pular tópicos bloqueados

            diversity_bonus = self.config["score_diversity_bonus"] if searches_6h == 0 else 0
            cache_penalty = searches_6h * self.config["score_cache_penalty"]

            final_score = base_score + diversity_bonus - cache_penalty

            topic_score = TopicScore(
                topic_id=-1,  # ID fictício para tópicos default
                topic_name=topic_name,
                score=final_score,
                user_count=0,
                news_count_7d=0,
                searches_6h=searches_6h,
                is_blocked=False
            )

            default_scores.append(topic_score)

        logging.info(f"Usando {len(default_scores)} tópicos default: {[t.topic_name for t in default_scores]}")
        return default_scores

    def get_score_breakdown(self, topic_name: str) -> Dict:
        """
        Retorna detalhamento do cálculo de score para um tópico específico.
        Útil para debugging e ajustes.

        Args:
            topic_name: Nome do tópico

        Returns:
            Dicionário com detalhes do cálculo
        """
        # Buscar métricas
        all_metrics = self.stats_repo.get_topic_metrics(days=7)
        topic_metrics = next((m for m in all_metrics if m.topic_name.lower() == topic_name.lower()), None)

        if not topic_metrics:
            return {"error": f"Tópico '{topic_name}' não encontrado"}

        # Calcular componentes
        config = self.config

        searches_6h = 0
        if self.cache:
            searches_6h = self.cache.count_searches_in_period(topic_name, hours=config["cache_ttl_hours"])

        is_blocked = searches_6h >= config["max_searches_per_topic_in_6h"]

        base_score = (
            topic_metrics.user_count * config["score_user_weight"]
            - topic_metrics.news_count_7d * config["score_news_weight"]
        )

        diversity_bonus = config["score_diversity_bonus"] if searches_6h == 0 else 0
        cache_penalty = searches_6h * config["score_cache_penalty"]

        final_score = -999999 if is_blocked else (base_score + diversity_bonus - cache_penalty)

        return {
            "topic_name": topic_name,
            "final_score": final_score,
            "is_blocked": is_blocked,
            "breakdown": {
                "user_count": topic_metrics.user_count,
                "user_contribution": topic_metrics.user_count * config["score_user_weight"],
                "news_count_7d": topic_metrics.news_count_7d,
                "news_penalty": topic_metrics.news_count_7d * config["score_news_weight"],
                "searches_6h": searches_6h,
                "diversity_bonus": diversity_bonus,
                "cache_penalty": cache_penalty,
                "base_score": base_score
            }
        }
