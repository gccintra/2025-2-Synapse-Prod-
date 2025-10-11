import logging
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Garante que os logs vão para o stdout do container
)

# ================================================================================
# SISTEMA DE COLETA INTELIGENTE DE NOTÍCIAS
# ================================================================================
#
# Este job utiliza um algoritmo de priorização de tópicos baseado em:
# - Interesse dos usuários (quantos usuários selecionaram cada tópico)
# - Cobertura atual (quantas notícias já temos de cada tópico)
# - Cache de buscas recentes (evita buscar o mesmo tópico repetidamente)
#
# APIs Externas e seus Limites:
# - GNews: 100 requisições/dia (configurável em news_collection_config.py)
# - Google Gemini (IA): 10 requisições/minuto, 200/dia (com throttling automático)
#
# Fluxo do Sistema:
# 1. Prioriza tópicos baseado em métricas do banco
# 2. Gera keywords para todos os tópicos em 1 única chamada Gemini (batch)
# 3. Faz 33 chamadas ao GNews: 1 top-headlines + 32 search (configurável)
# 4. Processa e salva todas as notícias
# 5. Categoriza notícias em batch (2 chamadas Gemini)
# 6. Total: ~3 chamadas Gemini e 33 GNews por execução
#
# Configurações:
# - Todas as configurações estão em: backend/app/config/news_collection_config.py
# - Ajuste quantidade de chamadas, tópicos, keywords, etc conforme necessário
#
# ================================================================================

def run_collection_job():
    """
    Executa o job de coleta inteligente de notícias.

    Utiliza o novo método collect_news_intelligently() que implementa:
    - Priorização automática de tópicos
    - Geração inteligente de keywords
    - Sistema de cache para evitar buscas repetitivas
    - Throttling rigoroso para respeitar limites de API
    """
    from app import create_app
    from app.services.news_collect_service import NewsCollectService

    app = create_app()
    with app.app_context():
        logging.info("=" * 80)
        logging.info("JOB DE COLETA INTELIGENTE INICIADO")
        logging.info("=" * 80)

        try:
            news_collect_service = NewsCollectService()

            # Usar novo método de coleta inteligente
            new_articles_count, new_sources_count = news_collect_service.collect_news_intelligently()

            logging.info("=" * 80)
            logging.info("JOB FINALIZADO COM SUCESSO")
            logging.info(f"Resumo: {new_articles_count} notícias e {new_sources_count} fontes salvas")
            logging.info("=" * 80)

        except Exception as e:
            logging.error("=" * 80)
            logging.error("ERRO CRÍTICO NO JOB DE COLETA")
            logging.error(f"Erro: {e}", exc_info=True)
            logging.error("=" * 80)
            raise  # Re-raise para que o cron job registre a falha

if __name__ == "__main__":
    run_collection_job()