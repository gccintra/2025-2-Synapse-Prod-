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

# ANÁLISE DE LIMITES DE API E ESTRATÉGIA DE CONTROLE DE FLUXO (THROTTLING)
#
# APIs Externas e seus Limites:
# - GNews: 100 requisições/dia.
# - Google Gemini (IA): 10 requisições/minuto.
#
# Lógica de Consumo:
# - 1 chamada à GNews retorna até 10 notícias.
# - Cada chamada ao Gnews consome 2 chamadas à API do Gemini (extração de tópicos + resumo).
#
# Gargalo e Estratégia:
# - O limite do Gemini (10 req/min) é o nosso principal gargalo. Ele nos permite
#   processar no máximo 5 chamadas ao Gnews por minuto (resultando em 50 notícias).
# - Para evitar exceder esse limite, o script implementa um "throttle":
#   a cada 5 chamadas ao gnews processadas, é introduzida uma pausa de 60 segundos.


# TODO: Implementar uma boa lógica para selecionar os topicos e palavras chaves das pesquisas, para nao pegar conteudo repetido ou irrelevante.
# TODO: selecionar os topicos mais escolhidos por usuarios, ou se nao tiver usar os topicos padrão do gnews.
# TODO: guardar em uma variavel quais topicos ja foram consumidos, em outras chamadas anteriores tambem (ultimas 6 horas) para nao ficar muito nichado.

def run_collection_job():
    from app import create_app
    from app.services.news_service import NewsService

    app = create_app()
    with app.app_context():
        logging.info("Iniciando o job de coleta de notícias...")


        try:
            news_service = NewsService()

            # TODO: Implementar lógica de seleção de tópicos em vez de uma lista fixa.

            test_topics = ["general"]
            new_articles_count, new_sources_count = news_service.collect_and_enrich_new_articles(topics=test_topics)
            logging.info(f"Job finalizado com sucesso. {new_articles_count} novas notícias e {new_sources_count} novas fontes foram salvas.")
        except Exception as e:
            logging.error(f"Ocorreu um erro inesperado durante a execução do job: {e}", exc_info=True)

if __name__ == "__main__":
    run_collection_job()