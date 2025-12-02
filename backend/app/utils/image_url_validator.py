"""
Utilitário para validação de acessibilidade de URLs de imagem.
Valida se URLs de imagem estão acessíveis antes de salvar artigos de notícias.
"""

import logging
import requests
from typing import Optional
from urllib.parse import urlparse


class ImageUrlValidator:
    """
    Valida se URLs de imagem são acessíveis antes de salvar notícias.

    Utiliza requisições HTTP HEAD para verificar rapidamente se uma URL
    de imagem está acessível sem baixar o conteúdo completo.
    """

    USER_AGENT = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/128.0.0.0 Safari/537.36'
    )

    @classmethod
    def validate_image_url_accessible(cls, url: str, timeout: int = 10) -> bool:
        """
        Valida se uma URL de imagem é acessível usando HTTP HEAD.

        Args:
            url: URL da imagem a ser validada
            timeout: Timeout em segundos (padrão: 10)

        Returns:
            True se acessível (status 200-299), False caso contrário

        Examples:
            >>> ImageUrlValidator.validate_image_url_accessible('https://example.com/image.jpg')
            True
            >>> ImageUrlValidator.validate_image_url_accessible('https://example.com/missing.jpg')
            False
        """
        if not url or not isinstance(url, str):
            logging.debug("URL de imagem vazia ou inválida")
            return False

        # Validação básica de formato URL
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                logging.debug(f"URL mal formada: {url}")
                return False
        except Exception as e:
            logging.debug(f"Erro ao fazer parse da URL {url}: {e}")
            return False

        try:
            headers = {'User-Agent': cls.USER_AGENT}

            # Usar HEAD request para eficiência
            response = requests.head(
                url,
                timeout=timeout,
                headers=headers,
                allow_redirects=True
            )

            # Aceitar códigos de sucesso (200-299)
            is_accessible = 200 <= response.status_code < 300

            if not is_accessible:
                logging.debug(
                    f"Imagem não acessível: {url} (status: {response.status_code})"
                )

            return is_accessible

        except requests.exceptions.Timeout:
            logging.debug(f"Timeout ao validar imagem: {url}")
            return False
        except requests.exceptions.ConnectionError as e:
            logging.debug(f"Erro de conexão ao validar imagem {url}: {e}")
            return False
        except requests.exceptions.RequestException as e:
            logging.debug(f"Erro de requisição ao validar imagem {url}: {e}")
            return False
        except Exception as e:
            logging.debug(f"Erro inesperado ao validar imagem {url}: {e}")
            return False

    @classmethod
    def get_domain(cls, url: str) -> Optional[str]:
        """
        Extrai o domínio de uma URL para análise e logging.

        Args:
            url: URL da qual extrair o domínio

        Returns:
            Domínio da URL ou None se inválida

        Examples:
            >>> ImageUrlValidator.get_domain('https://example.com/image.jpg')
            'example.com'
        """
        if not url or not isinstance(url, str):
            return None

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix se presente
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return None