import os
import requests
import json
import logging
from datetime import datetime
from newspaper import Article
from sqlalchemy.exc import IntegrityError
from newspaper.configuration import Configuration
from app.repositories.news_repository import NewsRepository
from app.repositories.user_news_repository import UserNewsRepository
from app.repositories.news_source_repository import NewsSourceRepository
from app.repositories.topic_repository import TopicRepository
from app.repositories.news_topic_repository import NewsTopicRepository
from app.services.ai_service import AIService
from app.services.topic_similarity_service import TopicSimilarityService
from app.models.news import News, NewsValidationError
from app.models.news_source import NewsSource
from app.models.topic import Topic, TopicValidationError
from app.models.exceptions import NewsSourceValidationError


# TODO: fazer consultas no banco para topicos mais selecionados e a partir desses topicos, pedir para IA criar palavras chaves para noticias e enviar para o endpoint de search.

# TODO: Tratar a quantidade de requests que vou fazer para cada topico, enviar um objeto com os topicos e varias informacoes do tipo

# TODO: adicionar parâmetro para dizer se vou rodar um top headlines ou um search por palavra chave

class NewsService():
    def __init__(
        self,
        news_repo: NewsRepository | None = None,
        news_source_repo: NewsSourceRepository | None = None,
        topic_repo: TopicRepository | None = None,
        news_topic_repo: NewsTopicRepository | None = None,
        ai_service: AIService | None = None,
        similarity_service: TopicSimilarityService | None = None,
        user_news_repo: UserNewsRepository | None = None
    ):
        self.news_repo = news_repo or NewsRepository()
        self.news_sources_repo = news_source_repo or NewsSourceRepository()
        self.topic_repo = topic_repo or TopicRepository()
        self.news_topic_repo = news_topic_repo or NewsTopicRepository()
        self.ai_service = ai_service or AIService()
        self.similarity_service = similarity_service or TopicSimilarityService(self.ai_service)
        self.gnews_api_key = os.getenv('GNEWS_API_KEY')
        self.api_endpoint = "https://gnews.io/api/v4/top-headlines"
        self.api_endpoint_search = "https://gnews.io/api/v4/search"
        self.user_news_repo = user_news_repo or UserNewsRepository()

        # Cache de tópicos existentes (TTL de 5 minutos)
        self._topics_cache = None
        self._topics_cache_timestamp = None
        self._topics_cache_ttl = 300  # 5 minutos em segundos

    # TODO: Nao devo receber uma lista de topicos, devo criar uma função para calcular quais topicos devem ser pesquisados, além de selecionar quantas consultas serão feitas em cada endpoint (search e top headlines)
    
    def collect_and_enrich_new_articles(self, topics: list[str] | None = None):
        if not self.gnews_api_key:
            logging.error("A variável de ambiente GNEWS_API_KEY não foi configurada.")
            raise ValueError("A variável de ambiente GNEWS_API_KEY não foi configurada.")

        all_articles_metadata = []

        search_topics = topics or [None]

        for topic in search_topics:
            logging.info(f"Buscando notícias para o tópico: {'Geral' if topic is None else topic}")
            articles_metadata = self.discover_articles_via_gnews(topic)
            all_articles_metadata.extend(articles_metadata)

        logging.info(f"Encontrados {len(all_articles_metadata)} artigos na API.")

        new_articles_count = 0
        new_sources_count = 0
        articles_to_categorize = []  # Lista de {news_id, content, title} para categorização em batch

        for i, article_meta in enumerate(all_articles_metadata, 1):
            title = article_meta.get('title')
            logging.info(f"Processando artigo {i}/{len(all_articles_metadata)}: '{title}'")
            article_url = article_meta.get('url')
            if not article_url:
                logging.warning("Artigo sem URL encontrado, pulando.")
                continue

            if self.news_repo.find_by_url(article_url):
                logging.info(f"Artigo já existe no banco de dados, pulando: {article_url}")
                continue

            source_name = article_meta.get('source', {}).get('name')
            source_url = article_meta.get('source', {}).get('url')

            if not source_name or not source_url:
                logging.warning(f"Pulando artigo por falta de dados da fonte: {article_url}")
                continue

            # Buscar fonte por URL primeiro
            news_source_model = self.news_sources_repo.find_by_url(source_url)

            # Se não encontrou por URL, buscar por nome (pode ter URL diferente)
            if not news_source_model:
                news_source_model = self.news_sources_repo.find_by_name(source_name)
                if news_source_model:
                    logging.info(f"Fonte '{source_name}' já existe com URL diferente. Usando fonte existente (ID={news_source_model.id}).")

            # Se não existe nem por URL nem por nome, criar nova
            if not news_source_model:
                try:
                    logging.info(f"Nova fonte encontrada: '{source_name}'. Criando no banco de dados.")
                    new_source = NewsSource(name=source_name, url=source_url)
                    news_source_model = self.news_sources_repo.create(new_source)
                    new_sources_count += 1
                except IntegrityError:
                    logging.warning(f"Race condition ao criar fonte '{source_name}'. Buscando novamente.")
                    # Tentar buscar por URL e por nome
                    news_source_model = self.news_sources_repo.find_by_url(source_url)
                    if not news_source_model:
                        news_source_model = self.news_sources_repo.find_by_name(source_name)
                    if not news_source_model:
                        logging.error(f"Não foi possível encontrar a fonte '{source_name}' após erro de integridade.")
                        continue
                except (NewsSourceValidationError, Exception) as e:
                    logging.error(f"Não foi possível criar a fonte '{source_name}': {e}", exc_info=True)
                    continue

            source_id = news_source_model.id

            article_content = self.scrape_article_content(article_url)
            if not article_content:
                logging.warning(f"Falha ao extrair conteúdo do artigo, pulando: {article_url}")
                continue

            try:
                published_at_str = article_meta.get('publishedAt')
                if published_at_str.endswith('Z'):
                    published_at_str = published_at_str[:-1] + '+00:00'
                published_at_dt = datetime.fromisoformat(published_at_str)

                article = News(
                    title=article_meta.get('title'),
                    url=article_url,
                    description=article_meta.get('description'),
                    content=article_content,
                    image_url=article_meta.get('image'),
                    published_at=published_at_dt,
                    source_id=source_id,
                )

                saved_article = self.news_repo.create(article)
                new_articles_count += 1
                logging.info(f"Novo artigo salvo: '{saved_article.title}'")

                articles_to_categorize.append({
                    'news_id': saved_article.id,
                    'content': saved_article.content,
                    'title': saved_article.title
                })

            except (NewsValidationError, Exception) as e:
                logging.error(f"Não foi possível criar o artigo '{article_meta.get('title')}': {e}", exc_info=True)
                continue

        # Categorizar todas as notícias em batch
        if articles_to_categorize:
            logging.info(f"Iniciando categorização em batch de {len(articles_to_categorize)} artigos")
            try:
                self._categorize_articles_batch(articles_to_categorize)
            except Exception as e:
                logging.error(f"Erro ao categorizar artigos em batch: {e}", exc_info=True)

        return new_articles_count, new_sources_count

    def discover_articles_via_gnews(self, topic: str | None = None, language='en', country='us', max_articles=10):
        params = {'lang': language, 'country': country, 'apikey': self.gnews_api_key, 'max': max_articles}
        if topic: params['category'] = topic

        try:
            response = requests.get(self.api_endpoint, params=params)
            response.raise_for_status()
            return response.json().get('articles', [])
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao chamar a GNews API: {e}", exc_info=True)
            return []

    def _get_all_topics_cached(self) -> list[Topic]:
        import time

        current_time = time.time()

        # Verifica se cache é válido
        if (self._topics_cache is not None and
            self._topics_cache_timestamp is not None and
            (current_time - self._topics_cache_timestamp) < self._topics_cache_ttl):
            logging.debug("Usando cache de tópicos")
            return self._topics_cache

        # Cache inválido ou inexistente, buscar do banco
        logging.debug("Atualizando cache de tópicos")
        self._topics_cache = self.topic_repo.list_all()
        self._topics_cache_timestamp = current_time

        return self._topics_cache

    def scrape_article_content(self, url: str) -> str | None:
        try:
            logging.debug(f"Fazendo scraping de: {url}")

            config = Configuration()
            config.browser_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
            config.request_timeout = 15
            config.keep_article_html = True

            article = Article(url, config=config)
            article.download()
            article.parse()
            return article.article_html
        except Exception as e:
            logging.error(f"Erro no scraping de {url}: {e}", exc_info=True)
            return None

    def favorite_news(self, user_id, news_id):
        return self.user_news_repo.set_favorite(user_id, news_id, is_favorite=True)

    def unfavorite_news(self, user_id, news_id):
        return self.user_news_repo.remove_favorite(user_id, news_id)
    def _extract_topics_from_content_batch(self, articles_data: list[dict], min_topics: int = 3) -> dict[int, list[str]]:
        if not articles_data:
            return {}

        # Construir o prompt para a IA
        articles_prompt_part = ""
        for article in articles_data:
            # Usar json.dumps para garantir que o conteúdo seja uma string JSON válida
            text_sample = article['content'][:5000]  # Limitar o tamanho do conteúdo
            articles_prompt_part += f'{{"id": {article["news_id"]}, "content": {json.dumps(text_sample)}}},\n'

        prompt = f"""Analise o conteúdo de cada notícia no array JSON abaixo e, para CADA UMA, extraia os principais **temas macro**.

**Regras Gerais:**
- Para cada notícia, retorne NO MÍNIMO {min_topics} tópicos macro.
- O tópico precisa ser na mesma linguagem da notícia enviada! (REGRA MÁXIMA) (se a noticia é em ingles, o topico precisa ser obrigatoriamente em inglês, se for em espanhol, o tópico precisa ser em espanhol)
- Cada tópico deve ter no MÁXIMO 3 palavras (é preferível que tenha somente 1 palavra).
- Os tópicos devem ser em letras minúsculas, sem pontuação e na mesma linguagem do conteúdo.
- Foque em temas macro (conceitos gerais) e não em detalhes específicos (micro).

Exemplo de extração bem feita:
**Conteúdo da notícia:** "O Comitê de Política Monetária (Copom) do Banco Central decidiu por unanimidade aumentar a taxa Selic em 0.5 ponto percentual, passando para 14% ao ano. A medida, segundo o presidente Roberto Campos, visa conter o avanço da inflação que tem pressionado o poder de compra das famílias."

**Temas a evitar (micro):**
- aumento da selic
- decisão do copom
- roberto campos

**Temas desejados (macro):**
- política 
- inflação
- economia 

---

**Formato de Saída OBRIGATÓRIO:**
Sua resposta deve ser um ÚNICO objeto JSON.
A chave do objeto deve ser o ID da notícia (como string).
O valor deve ser um array de strings com os tópicos extraídos.
Responda APENAS com o objeto JSON, sem nenhum texto adicional ou formatação de markdown (como ```json).

**Exemplo de Formato de Saída:**
{{
  "101": ["economia", "inflação", "política monetária"],
  "102": ["tecnologia", "inteligência artificial", "inovação"],
  "103": ["meio ambiente", "sustentabilidade", "energia renovável"]
}}

**Notícias para Análise (Array JSON):**
[{articles_prompt_part.rstrip(',\\n')}]

**Seu Objeto JSON de Resposta:**"""

        try:
            response_text = self.ai_service.generate_content(prompt)
            if not response_text:
                logging.warning("Resposta vazia da IA para extração de tópicos em batch.")
                return {article['news_id']: [] for article in articles_data}

            # Limpar a resposta para garantir que seja um JSON válido
            cleaned_response = response_text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]

            parsed_json = json.loads(cleaned_response)

            # Converter chaves de string para int e garantir que todos os IDs originais estejam presentes
            result = {article['news_id']: [] for article in articles_data}
            for news_id_str, topics in parsed_json.items():
                try:
                    news_id_int = int(news_id_str)
                    if news_id_int in result:
                        result[news_id_int] = topics
                except (ValueError, TypeError):
                    logging.warning(f"ID de notícia inválido '{news_id_str}' recebido da IA.")
            return result

        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON da IA para extração de tópicos: {e}", exc_info=True)
            logging.debug(f"Resposta recebida da IA: {response_text}")
            return {article['news_id']: [] for article in articles_data}
        except Exception as e:
            logging.error(f"Erro ao extrair tópicos em batch via IA: {e}", exc_info=True)
            return {article['news_id']: [] for article in articles_data}

    def _categorize_articles_batch(self, articles_data: list[dict]) -> dict[int, int]:
        if not articles_data:
            return {}

        logging.info(f"Iniciando categorização em batch de {len(articles_data)} artigos")

        # ETAPA 1: Extrair tópicos de todas as notícias (1 chamada de IA)
        try:
            logging.info(f"Extraindo tópicos de {len(articles_data)} artigos em uma única chamada de IA.")
            articles_topics = self._extract_topics_from_content_batch(articles_data)
            logging.info("Extração de tópicos em batch concluída.")
        except Exception as e:
            logging.error(f"Falha crítica na extração de tópicos em batch: {e}", exc_info=True)
            # Retorna 0 tópicos para todos os artigos se a extração em batch falhar
            return {article['news_id']: 0 for article in articles_data}

        all_extracted_topics = set()  # Todos os tópicos únicos extraídos
        for news_id, topic_names in articles_topics.items():
            if topic_names:
                all_extracted_topics.update(topic_names)
                logging.info(f"Artigo ID={news_id}: {len(topic_names)} tópicos extraídos: {topic_names}")

        if not all_extracted_topics:
            logging.warning("Nenhum tópico foi extraído de nenhum artigo")
            return {news_id: 0 for news_id in articles_topics.keys()}

        logging.info(f"Total de {len(all_extracted_topics)} tópicos únicos extraídos de todos os artigos")

        # ETAPA 2: Buscar tópicos existentes e verificar similaridade em BATCH (1 chamada de IA, se necessário)
        existing_topics = self._get_all_topics_cached()
        topic_mapping = {}  # {topic_name_extracted: Topic | None}

        # Primeiro, mapear tópicos com match exato
        for topic_name in all_extracted_topics:
            exact_match = self.topic_repo.find_by_name(topic_name)
            if exact_match:
                topic_mapping[topic_name] = exact_match
                logging.debug(f"Match exato: '{topic_name}' → ID={exact_match.id}")

        # Verificar quais tópicos ainda precisam de verificação de similaridade
        topics_to_check_similarity = [
            topic_name for topic_name in all_extracted_topics
            if topic_name not in topic_mapping
        ]

        if topics_to_check_similarity and existing_topics:
            logging.info(f"Verificando similaridade de {len(topics_to_check_similarity)} tópicos em batch")
            try:
                # UMA ÚNICA CHAMADA DE IA PARA VERIFICAR SIMILARIDADE DE TODOS OS TÓPICOS!
                similarity_results = self.similarity_service.find_similar_topics_batch(
                    topics_to_check_similarity,
                    existing_topics
                )

                # Adicionar resultados ao mapeamento
                for topic_name, similar_topic in similarity_results.items():
                    if similar_topic:
                        topic_mapping[topic_name] = similar_topic
                        logging.info(f"Similaridade detectada: '{topic_name}' → '{similar_topic.name}'")
                    else:
                        topic_mapping[topic_name] = None

            except Exception as e:
                logging.error(f"Erro ao verificar similaridade em batch: {e}", exc_info=True)
                # Em caso de erro, marcar todos como None (serão criados novos)
                for topic_name in topics_to_check_similarity:
                    topic_mapping[topic_name] = None
        else:
            # Não há tópicos para verificar similaridade
            for topic_name in topics_to_check_similarity:
                topic_mapping[topic_name] = None

        # ETAPA 3: Criar tópicos que não existem e não são similares
        topics_created = 0
        for topic_name, topic_model in topic_mapping.items():
            if topic_model is None:
                try:
                    logging.info(f"Criando novo tópico: '{topic_name}'")
                    new_topic = Topic(name=topic_name)
                    created_topic = self.topic_repo.create(new_topic)
                    topic_mapping[topic_name] = created_topic
                    topics_created += 1

                    # Adicionar ao cache
                    if self._topics_cache is not None:
                        self._topics_cache.append(created_topic)

                except IntegrityError:
                    # Race condition
                    logging.warning(f"Race condition ao criar tópico '{topic_name}'. Buscando novamente.")
                    existing = self.topic_repo.find_by_name(topic_name)
                    if existing:
                        topic_mapping[topic_name] = existing
                    else:
                        logging.error(f"Não foi possível criar ou encontrar tópico '{topic_name}'")
                        continue

                except (TopicValidationError, Exception) as e:
                    logging.error(f"Erro ao criar tópico '{topic_name}': {e}", exc_info=True)
                    continue

        logging.info(f"Criados {topics_created} novos tópicos")

        # ETAPA 4: Associar tópicos aos artigos
        result = {}
        for news_id, topic_names in articles_topics.items():
            topics_associated = 0

            for topic_name in topic_names:
                topic_model = topic_mapping.get(topic_name)

                if not topic_model:
                    logging.warning(f"Tópico '{topic_name}' não mapeado para artigo ID={news_id}")
                    continue

                try:
                    self.news_topic_repo.create_association(news_id, topic_model.id)
                    topics_associated += 1
                    logging.debug(f"Associado: news_id={news_id}, topic='{topic_name}'")

                except IntegrityError:
                    # Associação já existe
                    logging.debug(f"Associação já existe: news_id={news_id}, topic='{topic_name}'")
                    topics_associated += 1

                except Exception as e:
                    logging.error(f"Erro ao associar tópico '{topic_name}' ao artigo ID={news_id}: {e}", exc_info=True)

            result[news_id] = topics_associated
            logging.info(f"Artigo ID={news_id}: {topics_associated} tópicos associados")

        logging.info(f"Categorização em batch concluída: {len(result)} artigos processados")
        return result
