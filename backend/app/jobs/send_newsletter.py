import logging
import json
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from app import create_app
from app.repositories.user_repository import UserRepository
from app.services.newsletter_service import NewsletterService


def send_newsletter_job():
    app = create_app()

    with app.app_context():
        logging.info("=" * 80)
        logging.info("JOB DE ENVIO DE NEWSLETTER INICIADO")
        logging.info("=" * 80)

        try:
            user_repo = UserRepository()
            newsletter_service = NewsletterService()

            logging.info("Buscando usuários...")
            users = user_repo.get_users_to_newsletter()

            if not users:
                logging.info("Nenhum usuário manifestou interesse na newsletter. Finalizando.")
                return

            logging.info(f"Encontrados {len(users)} usuários para envio.")
            success_count = 0
            fail_count = 0

            for user in users:
                logging.info(f"--- Processando: {user.full_name} <{user.email}> ---")

                result = newsletter_service.send_newsletter_to_user(user)

                if result['success']:
                    success_count += 1
                else:
                    logging.warning(f"Falha no envio para {user.email}. Razão: {result['reason']}")
                    fail_count += 1

            logging.info("=" * 80)
            logging.info("JOB DE ENVIO DE NEWSLETTER FINALIZADO")
            logging.info(f"RESULTADO: {success_count} enviados com sucesso, {fail_count} falhas.")
            logging.info("=" * 80)

        except Exception as e:
            logging.critical(f"ERRO FATAL: O job terminou abruptamente: {e}", exc_info=True)
            raise
        



if __name__ == "__main__":
    send_newsletter_job()
