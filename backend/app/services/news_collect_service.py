import os
import requests
import logging
import time
from datetime import datetime
from newspaper import Article
from sqlalchemy.exc import IntegrityError
from newspaper.configuration import Configuration
from app.repositories.news_repository import NewsRepository
from app.repositories.news_source_repository import NewsSourceRepository
from app.repositories.topic_repository import TopicRepository
from app.models.news import News, NewsValidationError
from app.models.news_source import NewsSource
from app.models.exceptions import NewsSourceValidationError

from app.services.keyword_generation_service import KeywordGenerationService
from app.utils.scraping_blacklist import ScrapingBlacklist

class NewsCollectService():
    def __init__(
        self,
        news_repo: NewsRepository | None = None,
        news_source_repo: NewsSourceRepository | None = None,
        topic_repo: TopicRepository | None = None
    ):
        self.news_repo = news_repo or NewsRepository()
        self.news_sources_repo = news_source_repo or NewsSourceRepository()
        self.topic_repo = topic_repo or TopicRepository()

        self.keyword_service = KeywordGenerationService()
        self.blacklist = ScrapingBlacklist('/tmp/scraping_blacklist.json')
        self.blacklist.load

        self.gnews_api_key = os.getenv('GNEWS_API_KEY')
        self.api_endpoint = "https://gnews.io/api/v4/top-headlines"
        self.api_endpoint_search = "https://gnews.io/api/v4/search"


    def search_articles_via_gnews(self, query: str, language='pt', country='br', max_articles=10):
        params = {
            'q': query,
            'lang': language,
            'country': country,
            'apikey': self.gnews_api_key,
            'max': max_articles
        }

        max_retries = 2
        for attempt in range(max_retries):
            try:
                logging.info(f"GNews Search: query=\"{query}\", lang={language}, country={country}")
                response = requests.get(self.api_endpoint_search, params=params)

                # Se erro 429, aguardar e tentar novamente
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = 5
                        logging.warning(f"Erro 429 (Too Many Requests). Aguardando {wait_time}s antes de tentar novamente...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.error("Erro 429: limite de tentativas atingido")
                        return []

                response.raise_for_status()
                articles = response.json().get('articles', [])
                logging.info(f"GNews retornou {len(articles)} artigos")

                # Delay entre chamadas
                delay = 2  
                time.sleep(delay)

                return articles

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Erro ao chamar GNews (tentativa {attempt + 1}/{max_retries}): {e}")
                    time.sleep(5)
                else:
                    logging.error(f"Erro ao chamar GNews Search API: {e}", exc_info=True)
                    return []

        return []

    def call_top_headlines(self, category='general', language='pt', country='br', max_articles=10):
        params = {
            'category': category,
            'lang': language,
            'country': country,
            'apikey': self.gnews_api_key,
            'max': max_articles
        }

        max_retries = 2
        for attempt in range(max_retries):
            try:
                logging.info(f"GNews Top-Headlines: category={category}, lang={language}, country={country}")
                response = requests.get(self.api_endpoint, params=params)

                # Se erro 429, aguardar e tentar novamente
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = 5
                        logging.warning(f"Erro 429 (Too Many Requests). Aguardando {wait_time}s antes de tentar novamente...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.error("Erro 429: limite de tentativas atingido")
                        return []

                response.raise_for_status()
                articles = response.json().get('articles', [])
                logging.info(f"GNews retornou {len(articles)} artigos")

                # Delay entre chamadas
                delay = 2  
                time.sleep(delay)

                return articles

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Erro ao chamar GNews (tentativa {attempt + 1}/{max_retries}): {e}")
                    time.sleep(5)
                else:
                    logging.error(f"Erro ao chamar GNews Top-Headlines API: {e}", exc_info=True)
                    return []

        return []

    def collect_news_simple(self):
        """
        Método simplificado de coleta de notícias baseado em tópicos do banco de dados.

        Fluxo:
        1. Buscar tópicos ativos da tabela `topics`
        2. Para cada tópico 1 chamada para search usando keywords geradas por IA:
        3. Salvar notícias associadas ao topic_id correto

        Returns:
            Tupla (new_articles_count, new_sources_count)
        """
        if not self.gnews_api_key:
            logging.error("GNEWS_API_KEY não configurada")
            raise ValueError("GNEWS_API_KEY não configurada")

        logging.info("=" * 80)
        logging.info("INICIANDO COLETA SIMPLIFICADA DE NOTÍCIAS")
        logging.info("=" * 80)

        # PASSO 1: Buscar tópicos ativos do banco de dados
        logging.info("[1/3] Buscando tópicos ativos do banco de dados...")
        active_topics = self.topic_repo.list_all()  # Busca todos os tópicos ativos

        if not active_topics:
            logging.warning("Nenhum tópico ativo encontrado no banco de dados!")
            return (0, 0)

        logging.info(f"Encontrados {len(active_topics)} tópicos ativos: {[t.name for t in active_topics]}")

        # PASSO 2: Coleta por keywords para cada tópico
        logging.info(f"[2/3] Coletando notícias para {len(active_topics)} tópicos...")
        topic_articles_map = {}  # {topic_id: [articles]}
        total_articles_collected = 0
        total_gnews_calls = 0

        # 2.2: Geração de keywords em batch para todos os tópicos
        logging.info("    Gerando keywords para todos os tópicos em batch...")
        topic_names = [t.name for t in active_topics]
        try:
            keyword_results = self.keyword_service.generate_keywords_batch(topic_names)
            logging.info(f"    Keywords geradas para {len(keyword_results)} tópicos.")
        except Exception as e:
            logging.error(f"    Erro crítico ao gerar keywords em batch: {e}", exc_info=True)
            keyword_results = {}

        # 2.3: Busca por keywords para cada tópico
        for i, topic in enumerate(active_topics, 1):
            logging.info(f"  [{i}/{len(active_topics)}] Buscando notícias para o tópico: '{topic.name}' (ID={topic.id})")
            topic_lower = topic.name.lower()

            if topic_lower in keyword_results:
                topic_data = keyword_results[topic_lower]
                keywords = topic_data.get("keywords", [])
                language = topic_data.get("language", "en")
                country = topic_data.get("country", "us")

                if keywords:
                    query = self.keyword_service.build_boolean_query(keywords)
                    logging.info(f"    Query para '{topic.name}': {query}")

                    search_articles = self.search_articles_via_gnews(
                        query=query,
                        language=language,
                        country=country,
                        max_articles=10
                    )
                    topic_articles_map[topic.id] = search_articles
                    total_gnews_calls += 1
                    logging.info(f"    Search encontrou: {len(search_articles)} artigos")
                else:
                    logging.warning(f"    Nenhuma keyword gerada para '{topic.name}'. Pulando busca.")
            else:
                logging.warning(f"    Não foi possível obter keywords para '{topic.name}'. Pulando busca.")

        # Calcula o total de artigos coletados após as buscas
        for articles in topic_articles_map.values():
            total_articles_collected += len(articles)

        logging.info(f"Total de artigos coletados: {total_articles_collected}")
        logging.info(f"Total de chamadas GNews: {total_gnews_calls}")

        # PASSO 3: Processar e salvar notícias 
        logging.info("[3/3] Processando e salvando notícias...")
        new_articles_count = 0
        new_sources_count = 0

        for topic_id, articles_metadata in topic_articles_map.items():
            topic_name = next(t.name for t in active_topics if t.id == topic_id)
            logging.info(f"  Processando {len(articles_metadata)} artigos do tópico '{topic_name}'...")

            for i, article_meta in enumerate(articles_metadata, 1):
                title = article_meta.get('title', 'Título não disponível')
                article_url = article_meta.get('url')

                if not article_url:
                    logging.warning(f"    Artigo {i} sem URL. Pulando.")
                    continue

                if self.news_repo.find_by_url(article_url):
                    logging.debug(f"    Artigo {i} já existe: {article_url}")
                    continue

                source_name = article_meta.get('source', {}).get('name')
                source_url = article_meta.get('source', {}).get('url')

                if not source_name or not source_url:
                    logging.warning(f"    Artigo {i} sem dados de fonte. Pulando.")
                    continue

                # Scraping do conteúdo
                article_content = self.scrape_article_content(article_url)
                if not article_content:
                    logging.warning(f"    Falha no scraping: {article_url}")
                    continue

                # Buscar ou criar fonte
                news_source_model = self._get_or_create_source(source_name, source_url)
                if not news_source_model:
                    logging.error(f"    Não foi possível obter fonte para {source_name}")
                    continue

                if hasattr(news_source_model, '_is_new') and news_source_model._is_new:
                    new_sources_count += 1

                try:
                    published_at_str = article_meta.get('publishedAt')
                    if published_at_str and published_at_str.endswith('Z'):
                        published_at_str = published_at_str[:-1] + '+00:00'
                    published_at_dt = datetime.fromisoformat(published_at_str)

                    article = News(
                        title=title,
                        url=article_url,
                        description=article_meta.get('description'),
                        content=article_content,
                        image_url=article_meta.get('image'),
                        published_at=published_at_dt,
                        source_id=news_source_model.id,
                        topic_id=topic_id 
                    )

                    saved_article = self.news_repo.create(article)
                    new_articles_count += 1
                    logging.info(f"    Notícia salva: '{title[:50]}...' → tópico '{topic_name}' (ID={topic_id})")

                except Exception as e:
                    logging.error(f"    Erro ao salvar artigo '{title}': {e}")
                    continue

        logging.info("=" * 80)
        logging.info("COLETA SIMPLIFICADA FINALIZADA!")
        logging.info(f"RESUMO:")
        logging.info(f"  - Tópicos processados: {len(active_topics)} (do banco de dados)")
        logging.info(f"  - Estratégia: 1 busca por tópico com keywords de IA em batch")
        logging.info(f"  - Chamadas GNews: {total_gnews_calls}")
        logging.info(f"  - Artigos coletados: {total_articles_collected}")
        logging.info(f"  - Novos artigos salvos: {new_articles_count}")
        logging.info(f"  - Novas fontes: {new_sources_count}")
        logging.info("=" * 80)

        return (new_articles_count, new_sources_count)

    def _get_or_create_source(self, source_name: str, source_url: str):
        """Helper para buscar ou criar fonte de notícia"""
        news_source_model = self.news_sources_repo.find_by_url(source_url)

        if not news_source_model:
            news_source_model = self.news_sources_repo.find_by_name(source_name)
            if news_source_model:
                logging.info(f"Fonte '{source_name}' já existe com URL diferente (ID={news_source_model.id})")

        if not news_source_model:
            try:
                logging.info(f"Criando nova fonte: '{source_name}'")
                new_source = NewsSource(name=source_name, url=source_url)
                news_source_model = self.news_sources_repo.create(new_source)
                news_source_model._is_new = True  
            except IntegrityError:
                logging.warning(f"Race condition ao criar fonte '{source_name}'. Buscando novamente.")
                news_source_model = self.news_sources_repo.find_by_url(source_url)
                if not news_source_model:
                    news_source_model = self.news_sources_repo.find_by_name(source_name)
            except Exception as e:
                logging.error(f"Erro ao criar fonte '{source_name}': {e}")
                return None

        return news_source_model

    def scrape_article_content(self, url: str) -> str | None:
        """Scraping com blacklist para filtrar sites problemáticos"""
        try:
            # Verificar blacklist primeiro
            if self.blacklist.is_blocked(url):
                blocked_info = self.blacklist.get_blocked_info(url)
                logging.warning(f"Site bloqueado pela blacklist: {url} (motivo: {blocked_info.get('reason', 'N/A')})")
                return None

            logging.debug(f"Fazendo scraping de: {url}")

            config = Configuration()
            config.browser_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
            config.request_timeout = 30
            config.keep_article_html = True

            article = Article(url, config=config)
            article.download()
            article.parse()
            return article.article_html

        except Exception as e:
            error_msg = str(e)
            logging.error(f"Erro no scraping de {url}: {error_msg}")

            if any(error_code in error_msg for error_code in ['403', 'Forbidden', 'SSL', 'timeout', 'Timeout']):
                error_type = 'Unknown Error'
                if '403' in error_msg or 'Forbidden' in error_msg:
                    error_type = '403 Forbidden'
                elif 'SSL' in error_msg:
                    error_type = 'SSL Error'
                elif 'timeout' in error_msg or 'Timeout' in error_msg:
                    error_type = 'Timeout Error'

                self.blacklist.add_to_blacklist(
                    url=url,
                    error_type=error_type,
                    error_message=error_msg,
                    reason="Site blocks scraping or fails consistently"
                )

            return None
