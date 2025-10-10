"""
Script para popular o banco de dados com usuários e tópicos de interesse.
Útil para testar o sistema de priorização de coleta de notícias.

Uso:
    python backend/app/scripts/seed_users_topics.py
"""

import sys
import os

# Adicionar path do backend ao sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, backend_root)

from app import create_app
from app.extensions import db
from app.entities.user_entity import UserEntity
from app.entities.topic_entity import TopicEntity
from app.entities.user_topic_entity import UserTopicEntity
from app.models.user import User
from app.models.topic import Topic
from app.repositories.user_repository import UserRepository
from app.repositories.topic_repository import TopicRepository
from app.repositories.users_topics_repository import UsersTopicsRepository
import logging

logging.basicConfig(level=logging.INFO)

# Dados de exemplo (senha deve ter 8+ chars, maiúscula, minúscula e número)
SAMPLE_USERS = [
    {"full_name": "João Silva", "email": "joao.silva@example.com", "password": "Senha123"},
    {"full_name": "Maria Santos", "email": "maria.santos@example.com", "password": "Senha123"},
    {"full_name": "Pedro Oliveira", "email": "pedro.oliveira@example.com", "password": "Senha123"},
    {"full_name": "Ana Costa", "email": "ana.costa@example.com", "password": "Senha123"},
    {"full_name": "Carlos Souza", "email": "carlos.souza@example.com", "password": "Senha123"},
    {"full_name": "Julia Ferreira", "email": "julia.ferreira@example.com", "password": "Senha123"},
    {"full_name": "Lucas Almeida", "email": "lucas.almeida@example.com", "password": "Senha123"},
    {"full_name": "Beatriz Lima", "email": "beatriz.lima@example.com", "password": "Senha123"},
    {"full_name": "Rafael Pereira", "email": "rafael.pereira@example.com", "password": "Senha123"},
    {"full_name": "Camila Rodrigues", "email": "camila.rodrigues@example.com", "password": "Senha123"},
    {"full_name": "Fernando Dias", "email": "fernando.dias@example.com", "password": "Senha123"},
    {"full_name": "Juliana Martins", "email": "juliana.martins@example.com", "password": "Senha123"},
    {"full_name": "Thiago Barbosa", "email": "thiago.barbosa@example.com", "password": "Senha123"},
    {"full_name": "Patricia Gomes", "email": "patricia.gomes@example.com", "password": "Senha123"},
    {"full_name": "Rodrigo Fernandes", "email": "rodrigo.fernandes@example.com", "password": "Senha123"},
    {"full_name": "Amanda Carvalho", "email": "amanda.carvalho@example.com", "password": "Senha123"},
    {"full_name": "Bruno Monteiro", "email": "bruno.monteiro@example.com", "password": "Senha123"},
    {"full_name": "Fernanda Castro", "email": "fernanda.castro@example.com", "password": "Senha123"},
    {"full_name": "Gabriel Rocha", "email": "gabriel.rocha@example.com", "password": "Senha123"},
    {"full_name": "Larissa Azevedo", "email": "larissa.azevedo@example.com", "password": "Senha123"},
]

SAMPLE_TOPICS = [
    "technology",
    "crypto",
    "economy",
    "sports",
    "health",
    "study",
    "artifical inteligence",
    "science",
    "business",
    "culture",
    "imigrants",
    "art",
    "United States",
    "trap",
    "startup",
]

# Distribuição de interesses (tópicos mais populares têm mais usuários)
USER_TOPICS_DISTRIBUTION = {
    "technology": 15,      # 15 usuários interessados (75%)
    "crypto": 12,        # 12 usuários (60%)
    "economy": 10,        # 10 usuários (50%)
    "sports": 14,        # 14 usuários (70%)
    "health": 8,            # 8 usuários (40%)
    "study": 6,         # 6 usuários (30%)
    "artifical inteligence": 11,  # 11 usuários (55%)
    "science": 7,          # 7 usuários (35%)
    "business": 5,    # 5 usuários (25%)
    "culture": 9,          # 9 usuários (45%)
    "imigrants": 8,    # 8 usuários (40%)
    "art": 4,        # 4 usuários (20%)
    "United States": 6,         # 6 usuários (30%)
    "trap": 10,        # 10 usuários (50%)
    "startup": 7,          # 7 usuários (35%)
}


def create_or_get_topics(topic_repo: TopicRepository):
    """Cria ou busca tópicos no banco."""
    logging.info("Criando/buscando tópicos...")
    topics = {}

    for topic_name in SAMPLE_TOPICS:
        existing = topic_repo.find_by_name(topic_name)

        if existing:
            topics[topic_name] = existing
            logging.debug(f"Tópico '{topic_name}' já existe (ID={existing.id})")
        else:
            try:
                new_topic = Topic(name=topic_name)
                created = topic_repo.create(new_topic)
                topics[topic_name] = created
                logging.info(f"Tópico '{topic_name}' criado (ID={created.id})")
            except Exception as e:
                logging.error(f"Erro ao criar tópico '{topic_name}': {e}")
                # Tentar buscar novamente (race condition)
                existing = topic_repo.find_by_name(topic_name)
                if existing:
                    topics[topic_name] = existing

    logging.info(f"{len(topics)} tópicos prontos")
    return topics


def create_users(user_repo: UserRepository):
    """Cria usuários no banco."""
    logging.info("Criando usuários...")
    users = []

    for user_data in SAMPLE_USERS:
        existing = user_repo.find_by_email(user_data["email"])

        if existing:
            users.append(existing)
            logging.debug(f"Usuário '{user_data['email']}' já existe (ID={existing.id})")
        else:
            try:
                new_user = User(
                    full_name=user_data["full_name"],
                    email=user_data["email"],
                    password=user_data["password"]
                )
                created = user_repo.create(new_user)
                users.append(created)
                logging.info(f"Usuário '{user_data['email']}' criado (ID={created.id})")
            except Exception as e:
                logging.error(f"Erro ao criar usuário '{user_data['email']}': {e}")
                # Tentar buscar novamente
                existing = user_repo.find_by_email(user_data["email"])
                if existing:
                    users.append(existing)

    logging.info(f"{len(users)} usuários prontos")
    return users


def associate_users_with_topics(
    users: list,
    topics: dict,
    users_topics_repo: UsersTopicsRepository
):
    """Associa usuários com tópicos de interesse."""
    logging.info("Associando usuários com tópicos...")

    associations_created = 0
    associations_skipped = 0

    # Para cada tópico, associar N usuários aleatoriamente
    import random
    random.seed(42)  # Para resultados consistentes

    for topic_name, num_users in USER_TOPICS_DISTRIBUTION.items():
        if topic_name not in topics:
            logging.warning(f"Tópico '{topic_name}' não encontrado")
            continue

        topic = topics[topic_name]

        # Selecionar usuários aleatórios
        selected_users = random.sample(users, min(num_users, len(users)))

        for user in selected_users:
            try:
                users_topics_repo.attach(user.id, topic.id)
                associations_created += 1
                logging.debug(f"Associado: user={user.email}, topic={topic_name}")
            except Exception as e:
                # Associação já existe ou erro
                associations_skipped += 1
                logging.debug(f"Pulado: user={user.email}, topic={topic_name}")

    logging.info(f"Associações criadas: {associations_created}")
    logging.info(f"Associações puladas (já existiam): {associations_skipped}")


def print_statistics(topic_repo: TopicRepository):
    """Imprime estatísticas do banco."""
    from app.repositories.topic_stats_repository import TopicStatsRepository

    logging.info("\n" + "=" * 80)
    logging.info("ESTATÍSTICAS DO BANCO DE DADOS")
    logging.info("=" * 80)

    stats_repo = TopicStatsRepository()
    metrics = stats_repo.get_topic_metrics(days=365)  # Todos os dados

    # Ordenar por quantidade de usuários
    metrics_sorted = sorted(metrics, key=lambda m: m.user_count, reverse=True)

    logging.info(f"\n{'Tópico':<20} {'Usuários':<10} {'Notícias (7d)':<15}")
    logging.info("-" * 50)

    for metric in metrics_sorted:
        if metric.user_count > 0:  # Mostrar apenas tópicos com usuários
            logging.info(
                f"{metric.topic_name:<20} {metric.user_count:<10} {metric.news_count_7d:<15}"
            )

    summary = stats_repo.get_summary()
    logging.info("\n" + "=" * 80)
    logging.info("RESUMO")
    logging.info("=" * 80)
    logging.info(f"Total de tópicos: {summary['total_topics']}")
    logging.info(f"Tópicos com usuários: {summary['topics_with_users']}")
    logging.info(f"Total de interesses registrados: {summary['total_user_interests']}")
    logging.info(f"Notícias dos últimos 7 dias: {summary['total_news_7d']}")
    logging.info("=" * 80 + "\n")


def main():
    """Função principal."""
    logging.info("=" * 80)
    logging.info("INICIANDO SEED DE USUÁRIOS E TÓPICOS")
    logging.info("=" * 80)

    app = create_app()

    with app.app_context():
        # Repositories
        user_repo = UserRepository()
        topic_repo = TopicRepository()
        users_topics_repo = UsersTopicsRepository()

        # 1. Criar/buscar tópicos
        topics = create_or_get_topics(topic_repo)

        # 2. Criar usuários
        users = create_users(user_repo)

        # 3. Associar usuários com tópicos
        associate_users_with_topics(users, topics, users_topics_repo)

        # 4. Imprimir estatísticas
        print_statistics(topic_repo)

    logging.info("=" * 80)
    logging.info("SEED CONCLUÍDO COM SUCESSO!")
    logging.info("=" * 80)


if __name__ == "__main__":
    main()
