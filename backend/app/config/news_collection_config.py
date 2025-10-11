"""
Configurações para o sistema de coleta inteligente de notícias.
Todos os parâmetros podem ser ajustados aqui facilmente.
"""

NEWS_COLLECTION_CONFIG = {
    # ==========================================
    # QUANTIDADE DE CHAMADAS À API GNEWS
    # ==========================================
    "gnews_calls_per_job": 10,
    "gnews_top_headlines_calls": 1,  # Chamada obrigatória ao top-headlines
    "gnews_search_calls": 9,  # gnews_calls_per_job - gnews_top_headlines_calls

    # ==========================================
    # DISTRIBUIÇÃO DE TÓPICOS E KEYWORDS
    # ==========================================
    "topics_to_select": 9,  # Quantidade de tópicos prioritários a selecionar
    "searches_per_topic": 1,  # Quantidade de buscas por tópico (gnews_search_calls / topics_to_select)
    "keywords_per_search": 4,  # Quantidade de keywords por grupo/busca (REDUZIDO: queries menores = mais resultados)

    # ==========================================
    # SISTEMA DE CACHE
    # ==========================================
    "cache_ttl_hours": 6,  # Tempo de vida das entradas no cache (em horas)
    "max_searches_per_topic_in_6h": 3,  # Máximo de buscas por tópico nas últimas 6 horas
    "cache_file_path": "backend/app/data/topic_search_cache.json",

    # ==========================================
    # ALGORITMO DE PRIORIZAÇÃO (SCORING)
    # ==========================================
    "score_user_weight": 10,  # Peso de cada usuário interessado no tópico
    "score_news_weight": 0.5,  # Peso (negativo) de cada notícia já existente
    "score_diversity_bonus": 50,  # Bônus para tópicos não buscados nas últimas 6h
    "score_cache_penalty": 30,  # Penalidade por cada busca recente (multiplicado por search_count_6h)

    # ==========================================
    # IDIOMAS E PAÍSES
    # ==========================================
    "supported_languages": ["pt", "en"],  # Idiomas suportados no sistema
    "language_country_map": {
        "pt": "br",  # Português -> Brasil
        "en": "us"   # Inglês -> Estados Unidos
    },
    "default_language": "en",
    "default_country": "us",

    # ==========================================
    # TÓPICOS DEFAULT (FALLBACK)
    # ==========================================
    # Usados quando não há usuários com preferências
    "default_topics": [
        "technology", "politics", "economy", "health", "education",
        "sports", "entertainment", "science", "environment",
        "security", "international", "culture"
    ],

    # ==========================================
    # GNEWS API
    # ==========================================
    "gnews_max_articles_per_call": 10,  # Máximo de artigos por chamada (limite da API)
    "gnews_top_headlines_category": "general",  # Categoria para top-headlines
    "gnews_delay_between_calls": 2,  # Delay em segundos entre cada chamada (evita erro 429)

    # ==========================================
    # THROTTLING - GEMINI API
    # ==========================================
    "gemini_max_calls_per_minute": 10,  # Limite de chamadas por minuto do Gemini
    "gemini_rate_limit_window_seconds": 60,  # Janela de tempo do rate limit (segundos)
}


def get_config():
    """Retorna as configurações do sistema de coleta."""
    return NEWS_COLLECTION_CONFIG


def validate_config():
    """Valida se as configurações estão consistentes."""
    config = NEWS_COLLECTION_CONFIG

    # Validar distribuição de chamadas
    expected_search_calls = config["gnews_calls_per_job"] - config["gnews_top_headlines_calls"]
    if config["gnews_search_calls"] != expected_search_calls:
        raise ValueError(
            f"Inconsistência: gnews_search_calls ({config['gnews_search_calls']}) "
            f"deve ser igual a gnews_calls_per_job - gnews_top_headlines_calls ({expected_search_calls})"
        )

    # Validar distribuição de tópicos
    expected_searches = config["topics_to_select"] * config["searches_per_topic"]
    if config["gnews_search_calls"] != expected_searches:
        raise ValueError(
            f"Inconsistência: topics_to_select × searches_per_topic ({expected_searches}) "
            f"deve ser igual a gnews_search_calls ({config['gnews_search_calls']})"
        )

    return True


# Validar configurações ao importar o módulo
validate_config()
