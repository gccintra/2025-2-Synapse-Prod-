import os
import logging
import google.generativeai as genai


class AIService:
    def __init__(self, timeout: int = 60): 
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.timeout = timeout

        if not self.api_key:
            logging.warning("GEMINI_API_KEY não configurada. Serviço de IA desabilitado.")
            self.model = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(
                    'gemini-2.5-flash',
                    generation_config={
                        'temperature': 0.1, 
                    }
                )
                logging.info(f"AIService inicializado com sucesso (modelo=gemini-2.5-flash, timeout={self.timeout}s).")
            except Exception as e:
                logging.error(f"Erro ao inicializar o modelo Gemini: {e}", exc_info=True)
                self.model = None

    def generate_content(self, prompt: str) -> str | None:
        if not self.model:
            logging.warning("Modelo Gemini não disponível.")
            return None

        if not prompt or not isinstance(prompt, str) or len(prompt.strip()) == 0:
            logging.warning("Prompt inválido ou vazio.")
            return None

        try:
            logging.debug(f"Chamando API Gemini (timeout={self.timeout}s, prompt_len={len(prompt)})")

            # Chamar API com timeout via request_options
            response = self.model.generate_content(
                prompt,
                request_options={'timeout': self.timeout}
            )

            # Verificar se há resposta válida
            if not response or not hasattr(response, 'text'):
                logging.warning("Resposta inválida da API Gemini.")
                return None

            response_text = response.text
            logging.debug(f"API Gemini respondeu com sucesso (response_len={len(response_text)})")
            return response_text

        except Exception as e:
            logging.error(f"Erro ao chamar a API Gemini: {e}", exc_info=True)
            raise
