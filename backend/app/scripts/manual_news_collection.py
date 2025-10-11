"""
Script CLI para coleta manual de notícias.

Permite executar a coleta de notícias manualmente com parâmetros configuráveis,
útil para testes, debugging e experimentação.

Uso:
    python -m app.scripts.manual_news_collection [opções]

Exemplos:
    # Coleta inteligente padrão
    python -m app.scripts.manual_news_collection

    # Coleta customizada
    python -m app.scripts.manual_news_collection --topics-count 5 --verbose

    # Modo dry-run (simulação)
    python -m app.scripts.manual_news_collection --dry-run --verbose
"""

import argparse
import sys
import logging
from datetime import datetime
from app import create_app
from app.services.news_collect_service import NewsCollectService
from app.config.news_collection_config import get_config


def setup_logging(verbose=False):
    """Configura o sistema de logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def parse_arguments():
    """Configura e processa argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description='Coleta manual de notícias com parâmetros configuráveis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Coleta inteligente padrão
  python -m app.scripts.manual_news_collection

  # Coleta com parâmetros customizados
  python -m app.scripts.manual_news_collection --topics-count 5 --search-calls 10

  # Coleta em português/Brasil
  python -m app.scripts.manual_news_collection --language pt --country br

  # Modo dry-run (não salva no banco)
  python -m app.scripts.manual_news_collection --dry-run --verbose

  # Coleta legado com tópicos específicos
  python -m app.scripts.manual_news_collection --mode legacy --topics technology sports
        """
    )

    # Modo de operação
    parser.add_argument(
        '--mode',
        choices=['intelligent', 'legacy'],
        default='intelligent',
        help='Modo de coleta: intelligent (padrão) ou legacy'
    )

    # Parâmetros de configuração
    parser.add_argument(
        '--topics-count',
        type=int,
        help='Número de tópicos prioritários a selecionar (padrão: config)'
    )

    parser.add_argument(
        '--search-calls',
        type=int,
        help='Número de chamadas de search ao GNews (padrão: config)'
    )

    parser.add_argument(
        '--max-articles',
        type=int,
        help='Máximo de artigos por chamada (padrão: config)'
    )

    parser.add_argument(
        '--keywords-per-search',
        type=int,
        help='Número de keywords por busca (padrão: config)'
    )

    # Parâmetros de idioma/país
    parser.add_argument(
        '--language',
        help='Código do idioma (pt, en, etc) (padrão: config)'
    )

    parser.add_argument(
        '--country',
        help='Código do país (br, us, etc) (padrão: config)'
    )

    parser.add_argument(
        '--category',
        help='Categoria para top-headlines (padrão: config)'
    )

    # Parâmetros específicos do modo legacy
    parser.add_argument(
        '--topics',
        nargs='+',
        help='Tópicos específicos para modo legacy (ex: technology sports)'
    )

    # Flags
    parser.add_argument(
        '--skip-cache',
        action='store_true',
        help='Ignorar cache de buscas'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Modo simulação (não salva no banco de dados)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Modo verbose com logs detalhados'
    )

    return parser.parse_args()


def override_config(args):
    """
    Cria uma configuração customizada baseada nos argumentos.
    Não modifica a configuração global.
    """
    config = get_config().copy()

    # Aplicar overrides
    if args.topics_count:
        config['topics_to_select'] = args.topics_count

    if args.search_calls:
        config['gnews_search_calls'] = args.search_calls

    if args.max_articles:
        config['gnews_max_articles_per_call'] = args.max_articles

    if args.keywords_per_search:
        config['keywords_per_search'] = args.keywords_per_search

    if args.language:
        config['default_language'] = args.language

    if args.country:
        config['default_country'] = args.country

    if args.category:
        config['gnews_top_headlines_category'] = args.category

    return config


def print_config_summary(config, args):
    """Exibe resumo das configurações que serão usadas."""
    print("\n" + "=" * 80)
    print("CONFIGURAÇÕES DA COLETA")
    print("=" * 80)
    print(f"Modo: {args.mode.upper()}")

    if args.mode == 'intelligent':
        print(f"Tópicos a selecionar: {config['topics_to_select']}")
        print(f"Chamadas de search: {config['gnews_search_calls']}")
        print(f"Keywords por busca: {config['keywords_per_search']}")
    elif args.mode == 'legacy' and args.topics:
        print(f"Tópicos específicos: {', '.join(args.topics)}")

    print(f"Artigos por chamada: {config['gnews_max_articles_per_call']}")
    print(f"Idioma: {config['default_language']}")
    print(f"País: {config['default_country']}")
    print(f"Categoria top-headlines: {config['gnews_top_headlines_category']}")

    if args.skip_cache:
        print("Cache: DESABILITADO")

    if args.dry_run:
        print("\n⚠️  MODO DRY-RUN: Nenhuma alteração será salva no banco de dados")

    print("=" * 80 + "\n")


def run_intelligent_collection(args, config):
    """Executa coleta inteligente de notícias."""
    logging.info("Iniciando coleta inteligente de notícias...")

    # Criar serviço com configuração customizada
    service = NewsCollectService()

    # Aplicar configuração temporária
    service.config = config

    # Limpar cache se solicitado
    if args.skip_cache:
        logging.info("Limpando cache antes da coleta...")
        service.cache.clear()
        service.cache.save()

    # Executar coleta
    if args.dry_run:
        logging.warning("Modo dry-run: simulação apenas, nada será salvo")
        # TODO: Implementar modo dry-run
        logging.info("Dry-run não implementado ainda para modo intelligent")
        return (0, 0)

    return service.collect_news_intelligently()


def run_legacy_collection(args, config):
    """Executa coleta legado de notícias."""
    logging.info("Iniciando coleta legado de notícias...")

    service = NewsCollectService()
    topics = args.topics if args.topics else None

    if args.dry_run:
        logging.warning("Modo dry-run: simulação apenas, nada será salvo")
        # TODO: Implementar modo dry-run
        logging.info("Dry-run não implementado ainda para modo legacy")
        return (0, 0)

    return service.collect_and_enrich_new_articles(topics=topics)


def print_summary(new_articles, new_sources, elapsed_time):
    """Exibe resumo final da coleta."""
    print("\n" + "=" * 80)
    print("RESUMO DA COLETA")
    print("=" * 80)
    print(f"Novos artigos: {new_articles}")
    print(f"Novas fontes: {new_sources}")
    print(f"Tempo decorrido: {elapsed_time:.2f}s")
    print("=" * 80 + "\n")


def main():
    """Função principal do script."""
    args = parse_arguments()
    setup_logging(args.verbose)

    # Exibir banner
    print("\n" + "=" * 80)
    print("COLETA MANUAL DE NOTÍCIAS - SYNAPSE")
    print("=" * 80 + "\n")

    # Criar configuração customizada
    config = override_config(args)

    # Exibir configurações
    print_config_summary(config, args)

    # Criar contexto da aplicação Flask
    app = create_app()

    with app.app_context():
        start_time = datetime.now()

        try:
            # Executar coleta baseado no modo
            if args.mode == 'intelligent':
                new_articles, new_sources = run_intelligent_collection(args, config)
            else:  # legacy
                new_articles, new_sources = run_legacy_collection(args, config)

            # Calcular tempo decorrido
            elapsed_time = (datetime.now() - start_time).total_seconds()

            # Exibir resumo
            print_summary(new_articles, new_sources, elapsed_time)

            logging.info("Coleta finalizada com sucesso!")
            return 0

        except KeyboardInterrupt:
            print("\n\n⚠️  Coleta interrompida pelo usuário")
            return 130
        except Exception as e:
            logging.error(f"Erro durante a coleta: {e}", exc_info=True)
            return 1


if __name__ == "__main__":
    sys.exit(main())
