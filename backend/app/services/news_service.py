from app.repositories.news_repository import NewsRepository
from app.repositories.news_source_repository import NewsSourceRepository
from app.models.news import News, NewsValidationError
from app.models.news_source import NewsSource, NewsSourceValidationError
from app.models.exceptions import NewsNotFoundError
from typing import Optional


class NewsService():
    """
    Serviço responsável pela apresentação e busca de notícias.

    Responsabilidades:
    - Buscar notícias no banco de dados
    - Filtrar notícias por tópico, fonte, data
    - Paginar resultados
    - Retornar detalhes de notícias específicas

    Nota: A lógica de coleta de notícias foi movida para NewsCollectService
    """
    def __init__(self, news_repo: NewsRepository | None = None):
        self.news_repo = news_repo or NewsRepository()

    def get_news_by_id(self, user_id: int, news_id: int) -> dict:
        news = self.news_repo.find_by_id(news_id, user_id=user_id)
        if not news:
            raise NewsNotFoundError(f"Notícia com ID {news_id} não encontrada.")

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
            "is_favorited": news.is_favorited, # Adiciona o campo de favorito
        }

        # Incluir nome da fonte se disponível
        if news.source_name:
            news_dict["source_name"] = news.source_name

        return news_dict

    def get_news_for_user(self, user_id: Optional[int], page: int = 1, per_page: int = 10):
        """
        Retorna notícias paginadas para um usuário.

        Args:
            user_id: ID do usuário
            page: Número da página (começa em 1)
            per_page: Quantidade de itens por página

        Returns:
            Dict com notícias, paginação e metadados
        """
        # TODO: Implementar filtros baseados nas preferências do usuário
        # Por enquanto retorna todas as notícias paginadas usando list_all do repositório

        # Buscar notícias paginadas
        paginated_news = self.news_repo.list_all(page=page, per_page=per_page, user_id=user_id)

        # Contar total de notícias
        total_count = self.news_repo.count_all()

        # Converter objetos News para dicionários
        news_list = []
        for news in paginated_news:
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
                "is_favorited": news.is_favorited, # Adiciona o campo de favorito
            }

            # Incluir nome da fonte se disponível
            if news.source_name:
                news_dict["source_name"] = news.source_name

            news_list.append(news_dict)

        # Calcular total de páginas
        import math
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

    # TODO: Implementar métodos adicionais de busca e apresentação:
    # - get_news_by_topic(topic_id, pagination)
    # - get_news_by_source(source_id, pagination)
    # - search_news(query, filters, pagination)
