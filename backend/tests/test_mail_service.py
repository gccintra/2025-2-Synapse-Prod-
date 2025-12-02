import pytest
from unittest.mock import patch, MagicMock
import os
import smtplib
import logging

from app.services.mail_service import MailService


@pytest.fixture
def mock_env_vars():
    """Fixture para mockar as variáveis de ambiente do Gmail."""
    with patch.dict(os.environ, {
        'GMAIL_SENDER_EMAIL': 'test_user@gmail.com',
        'GMAIL_APP_PASSWORD': 'testpassword'
    }):
        yield


@pytest.fixture
def mock_smtplib():
    with patch('app.services.mail_service.smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        yield mock_server


def test_init_success(mock_env_vars):
    """Testa a inicialização bem-sucedida do MailService."""
    service = MailService()
    assert service.smtp_user == 'test_user@gmail.com'
    assert service.smtp_password == 'testpassword'
    assert service.smtp_host == 'smtp.gmail.com'
    assert service.smtp_port == 587


def test_init_missing_credentials(caplog):
    """Testa se um EnvironmentError é levantado quando as credenciais estão ausentes."""
    # Garante que as variáveis não estejam definidas
    if 'GMAIL_SENDER_EMAIL' in os.environ:
        del os.environ['GMAIL_SENDER_EMAIL']
    if 'GMAIL_APP_PASSWORD' in os.environ:
        del os.environ['GMAIL_APP_PASSWORD']

    with caplog.at_level(logging.ERROR):
        with pytest.raises(EnvironmentError, match="Credenciais do Gmail não configuradas."):
            MailService()
        assert "ERRO: Variáveis GMAIL_SENDER_EMAIL ou GMAIL_APP_PASSWORD vazias." in caplog.text


def test_sendemail_success(mock_env_vars, mock_smtplib, caplog):
    """Testa o envio de um e-mail bem-sucedido."""
    caplog.set_level(logging.INFO)
    service = MailService()

    recipient_email = "recipient@example.com"
    recipient_name = "Test Recipient"
    subject = "Test Subject"
    html_content = "<h1>Hello World</h1>"

    result = service.sendemail(recipient_email, recipient_name, subject, html_content)

    assert result is True

    # Verifica se o servidor SMTP foi chamado corretamente
    mock_smtplib.starttls.assert_called_once()
    mock_smtplib.login.assert_called_once_with('test_user@gmail.com', 'testpassword')
    mock_smtplib.sendmail.assert_called_once()
    mock_smtplib.quit.assert_called_once()

    # Verifica o conteúdo do e-mail enviado
    args, _ = mock_smtplib.sendmail.call_args
    sent_from = args[0]
    sent_to = args[1]
    message_as_string = args[2]

    assert sent_from == 'test_user@gmail.com'
    assert sent_to == recipient_email
    assert f"To: {recipient_email}" in message_as_string
    assert f"Subject: {subject}" in message_as_string
    assert html_content in message_as_string

    assert f"E-mail enviado via Gmail para: {recipient_email}" in caplog.text


def test_sendemail_failure(mock_env_vars, mock_smtplib, caplog):
    """Testa a falha no envio de e-mail devido a um erro no SMTP."""
    caplog.set_level(logging.ERROR)
    service = MailService()

    # Simula uma exceção durante o login
    error_message = "Authentication failed"
    mock_smtplib.login.side_effect = smtplib.SMTPAuthenticationError(535, error_message)

    recipient_email = "recipient@example.com"
    result = service.sendemail(recipient_email, "Test", "Subject", "Content")

    assert result is False
    mock_smtplib.quit.assert_not_called()  # quit() não deve ser chamado se houver erro antes

    assert "Falha de Autenticação" in caplog.text