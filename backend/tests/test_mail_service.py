import pytest
from unittest.mock import patch, MagicMock
import os
import smtplib
import logging

from app.services.mail_service import MailService


@pytest.fixture
def mock_env_vars():
    """Fixture para mockar as variáveis de ambiente do Mailtrap."""
    with patch.dict(os.environ, {
        'MAILTRAP_USER': 'test_user',
        'MAILTRAP_PASSWORD': 'test_password'
    }):
        yield


@pytest.fixture
def mock_smtplib():
    """Fixture para mockar a biblioteca smtplib."""
    with patch('app.services.mail_service.smtplib.SMTP') as mock_smtp:
        # O construtor SMTP retorna uma instância do servidor mockado
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        yield mock_server


def test_init_success(mock_env_vars):
    """Testa a inicialização bem-sucedida do MailService com variáveis de ambiente."""
    service = MailService()
    assert service.smtp_user == 'test_user'
    assert service.smtp_password == 'test_password'
    assert service.smtp_host == 'smtp.mailtrap.io'
    assert service.smtp_port == 2525


def test_init_missing_credentials(caplog):
    """Testa se um EnvironmentError é levantado quando as credenciais estão ausentes."""
    # Garante que as variáveis não estejam definidas
    if 'MAILTRAP_USER' in os.environ:
        del os.environ['MAILTRAP_USER']
    if 'MAILTRAP_PASSWORD' in os.environ:
        del os.environ['MAILTRAP_PASSWORD']

    with caplog.at_level(logging.ERROR):
        with pytest.raises(EnvironmentError, match="Credenciais Mailtrap não configuradas no ambiente."):
            MailService()
        assert "Variáveis MAILTRAP_USER ou MAILTRAP_PASSWORD não configuradas." in caplog.text


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
    mock_smtplib.login.assert_called_once_with('test_user', 'test_password')
    mock_smtplib.sendmail.assert_called_once()
    mock_smtplib.quit.assert_called_once()

    # Verifica o conteúdo do e-mail enviado
    args, _ = mock_smtplib.sendmail.call_args
    sent_from = args[0]
    sent_to = args[1]
    message_as_string = args[2]

    assert sent_from == 'test_user'
    assert sent_to == recipient_email
    assert f"To: {recipient_email}" in message_as_string
    assert f"Subject: {subject}" in message_as_string
    assert html_content in message_as_string

    assert f"E-mail enviado com sucesso para: {recipient_email}" in caplog.text


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

    assert f"Erro ao enviar e-mail para {recipient_email}" in caplog.text
    assert error_message in caplog.text