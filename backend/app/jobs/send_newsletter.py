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
from app.services.ai_service import AIService


def gerar_texto_intro(ai_service, user, news_data) -> str:
    """
    Função de compatibilidade para manter a interface antiga dos testes.

    DEPRECATED: Use NewsletterService.generate_newsletter_content() para melhor eficiência.
    Esta função mantém compatibilidade com testes existentes.
    """
    try:
        # Criar instância do NewsletterService para usar novo método
        newsletter_service = NewsletterService(ai_service=ai_service)
        ai_content = newsletter_service.generate_newsletter_content(user, news_data)

        if ai_content and 'intro' in ai_content:
            return ai_content['intro']
        else:
            # Fallback em inglês para manter consistência
            return f"Hello {user.full_name}, here's your personalized selection of this week's most important news."

    except Exception as e:
        logging.warning(f"Erro na função de compatibilidade gerar_texto_intro: {e}")
        return f"Hello {user.full_name}, here's your personalized selection of this week's most important news."


def build_newsletter_email(user_name, ai_content, news_items):
    """
    Função de compatibilidade para manter a interface antiga dos testes.

    DEPRECATED: Use NewsletterService.build_newsletter_email() para melhor eficiência.
    Esta função mantém compatibilidade com testes existentes.
    """
    try:
        # Criar instância do NewsletterService para usar novo método
        newsletter_service = NewsletterService()
        return newsletter_service.build_newsletter_email(user_name, ai_content, news_items)

    except Exception as e:
        logging.error(f"Erro na função de compatibilidade build_newsletter_email: {e}")
        return "<html><body><h1>Error generating newsletter</h1></body></html>"


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
