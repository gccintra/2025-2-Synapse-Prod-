import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MailService:
    def __init__(self):
        # 1. Lê as variáveis exatas do seu .env
        self.smtp_user = os.getenv('GMAIL_SENDER_EMAIL')      
        raw_password = os.getenv('GMAIL_APP_PASSWORD')        
        
        # 2. Configurações do Gmail
        self.smtp_host = 'smtp.gmail.com'
        self.smtp_port = 587

        # Validação básica
        if not self.smtp_user or not raw_password:
            logging.error("ERRO: Variáveis GMAIL_SENDER_EMAIL ou GMAIL_APP_PASSWORD vazias.")
            raise EnvironmentError("Credenciais do Gmail não configuradas.")
            
        # 3. Tratamento da senha: Remove os espaços em branco da senha de app
        self.smtp_password = raw_password.replace(" ", "")

    def sendemail(self, recipient_email: str, recipient_name: str,
              subject: str, html_content: str) -> bool:
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.smtp_user
            message['To'] = recipient_email

            part = MIMEText(html_content, 'html')
            message.attach(part)

            # Conexão com o Gmail
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls() # Criptografia TLS obrigatória
            
            # Login
            server.login(self.smtp_user, self.smtp_password)
            
            # Envio
            server.sendmail(self.smtp_user, recipient_email, message.as_string())
            server.quit()

            logging.info(f"E-mail enviado via Gmail para: {recipient_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logging.error("Falha de Autenticação: Verifique se a Senha de App está correta e se a verificação em 2 etapas está ativa.")
            return False
        except Exception as e:
            logging.error(f"Erro ao enviar e-mail: {e}", exc_info=True)
            return False