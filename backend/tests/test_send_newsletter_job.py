import pytest
from unittest.mock import patch, MagicMock, call
import logging

from app.jobs.send_newsletter import send_newsletter_job

# Mock de dados para os testes
class MockUser:
    def __init__(self, id, full_name, email):
        self.id = id
        self.full_name = full_name
        self.email = email

MOCK_USER_1 = MockUser(id=1, full_name="John Doe", email="john.doe@test.com")
MOCK_USER_2 = MockUser(id=2, full_name="Jane Smith", email="jane.smith@test.com")


@pytest.fixture
def mock_services():
    """Fixture para mockar todos os serviços e repositórios usados pelo job."""
    with patch('app.jobs.send_newsletter.UserRepository') as MockUserRepo, \
         patch('app.jobs.send_newsletter.NewsletterService') as MockNewsletterService, \
         patch('app.jobs.send_newsletter.create_app') as mock_create_app:

        # Configurar o mock do app_context
        mock_app = MagicMock()
        mock_app.app_context.return_value.__enter__.return_value = None
        mock_app.app_context.return_value.__exit__.return_value = None
        mock_create_app.return_value = mock_app

        yield {
            "user_repo": MockUserRepo.return_value,
            "newsletter_service": MockNewsletterService.return_value,
        }

def test_send_newsletter_job_happy_path(mock_services, caplog):
    caplog.set_level(logging.INFO)

    mock_services["user_repo"].get_users_to_newsletter.return_value = [MOCK_USER_1, MOCK_USER_2]
    mock_services["newsletter_service"].send_newsletter_to_user.return_value = {'success': True}

    send_newsletter_job()

    assert mock_services["user_repo"].get_users_to_newsletter.call_count == 1
    assert mock_services["newsletter_service"].send_newsletter_to_user.call_count == 2
    mock_services["newsletter_service"].send_newsletter_to_user.assert_has_calls([
        call(MOCK_USER_1),
        call(MOCK_USER_2)
    ])

    assert "JOB DE ENVIO DE NEWSLETTER FINALIZADO" in caplog.text
    assert "RESULTADO: 2 enviados com sucesso, 0 falhas." in caplog.text

def test_send_newsletter_job_no_users(mock_services, caplog):
    caplog.set_level(logging.INFO)
    mock_services["user_repo"].get_users_to_newsletter.return_value = []

    send_newsletter_job()

    assert "Nenhum usuário manifestou interesse na newsletter. Finalizando." in caplog.text
    assert mock_services["newsletter_service"].send_newsletter_to_user.call_count == 0

def test_send_newsletter_job_email_send_fails(mock_services, caplog):
    caplog.set_level(logging.INFO)
    mock_services["user_repo"].get_users_to_newsletter.return_value = [MOCK_USER_1]
    mock_services["newsletter_service"].send_newsletter_to_user.return_value = {'success': False, 'reason': 'SMTP Error'}

    send_newsletter_job()

    assert mock_services["newsletter_service"].send_newsletter_to_user.call_count == 1
    assert f"Falha no envio para {MOCK_USER_1.email}. Razão: SMTP Error" in caplog.text
    assert "RESULTADO: 0 enviados com sucesso, 1 falhas." in caplog.text

def test_send_newsletter_job_exception_during_user_processing(mock_services, caplog):
    caplog.set_level(logging.INFO)
    mock_services["user_repo"].get_users_to_newsletter.return_value = [MOCK_USER_1, MOCK_USER_2]
    
    mock_services["newsletter_service"].send_newsletter_to_user.side_effect = [
        {'success': False, 'reason': 'Exception: Erro de rede!'},
        {'success': True}
    ]

    send_newsletter_job()

    assert f"Falha no envio para {MOCK_USER_1.email}. Razão: Exception: Erro de rede!" in caplog.text
    assert mock_services["newsletter_service"].send_newsletter_to_user.call_count == 2
    assert "RESULTADO: 1 enviados com sucesso, 1 falhas." in caplog.text
