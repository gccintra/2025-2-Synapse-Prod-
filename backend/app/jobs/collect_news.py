import logging
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout  
)

def run_collection_job():
    """
    Executa o job de coleta simplificada de notícias.

    Utiliza o método collect_news_simple() que implementa:
    - Busca tópicos ativos do banco de dados
    - 2 chamadas GNews por tópico (top-headlines + search com keywords IA)
    - Salva notícias associadas ao topic_id correto
    - Lógica simples e eficiente sem complexidade desnecessária
    """
    from app import create_app
    from app.services.news_collect_service import NewsCollectService

    app = create_app()
    with app.app_context():
        logging.info("=" * 80)
        logging.info("JOB DE COLETA SIMPLIFICADA INICIADO")
        logging.info("=" * 80)

        try:
            news_collect_service = NewsCollectService()

            new_articles_count, new_sources_count = news_collect_service.collect_news_simple()

            logging.info("=" * 80)
            logging.info("JOB FINALIZADO COM SUCESSO")
            logging.info(f"Resumo: {new_articles_count} notícias e {new_sources_count} fontes salvas")
            logging.info("=" * 80)

        except Exception as e:
            logging.error("=" * 80)
            logging.error("ERRO CRÍTICO NO JOB DE COLETA")
            logging.error(f"Erro: {e}", exc_info=True)
            logging.error("=" * 80)
            raise  

if __name__ == "__main__":
    run_collection_job()