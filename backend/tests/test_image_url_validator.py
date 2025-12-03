import pytest
from unittest.mock import patch, Mock
import requests

from app.utils.image_url_validator import ImageUrlValidator


@pytest.fixture
def mock_requests_head():
    """Fixture para mockar requisições HEAD do requests."""
    with patch('app.utils.image_url_validator.requests.head') as mock_head:
        yield mock_head


@pytest.fixture
def mock_logging():
    """Fixture para mockar logging."""
    with patch('app.utils.image_url_validator.logging') as mock_log:
        yield mock_log


class TestImageUrlValidator:
    """Testes para o validador de URLs de imagem."""

    def test_validate_image_url_accessible_success(self, mock_requests_head):
        """Testa validação bem-sucedida de URL de imagem."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests_head.return_value = mock_response

        # Act
        result = ImageUrlValidator.validate_image_url_accessible('https://example.com/image.jpg')

        # Assert
        assert result is True
        mock_requests_head.assert_called_once_with(
            'https://example.com/image.jpg',
            timeout=10,
            headers={'User-Agent': ImageUrlValidator.USER_AGENT},
            allow_redirects=True
        )

    def test_validate_image_url_accessible_404_error(self, mock_requests_head, mock_logging):
        """Testa URL que retorna 404."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_requests_head.return_value = mock_response

        # Act
        result = ImageUrlValidator.validate_image_url_accessible('https://example.com/missing.jpg')

        # Assert
        assert result is False
        mock_logging.debug.assert_called_with(
            'Imagem não acessível: https://example.com/missing.jpg (status: 404)'
        )

    def test_validate_image_url_accessible_500_error(self, mock_requests_head, mock_logging):
        """Testa URL que retorna erro 500."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests_head.return_value = mock_response

        # Act
        result = ImageUrlValidator.validate_image_url_accessible('https://example.com/error.jpg')

        # Assert
        assert result is False
        mock_logging.debug.assert_called_with(
            'Imagem não acessível: https://example.com/error.jpg (status: 500)'
        )

    def test_validate_image_url_accessible_timeout(self, mock_requests_head, mock_logging):
        """Testa timeout da requisição."""
        # Arrange
        mock_requests_head.side_effect = requests.exceptions.Timeout()

        # Act
        result = ImageUrlValidator.validate_image_url_accessible('https://slow-site.com/image.jpg')

        # Assert
        assert result is False
        mock_logging.debug.assert_called_with(
            'Timeout ao validar imagem: https://slow-site.com/image.jpg'
        )

    def test_validate_image_url_accessible_connection_error(self, mock_requests_head, mock_logging):
        """Testa erro de conexão."""
        # Arrange
        mock_requests_head.side_effect = requests.exceptions.ConnectionError()

        # Act
        result = ImageUrlValidator.validate_image_url_accessible('https://unreachable.com/image.jpg')

        # Assert
        assert result is False
        mock_logging.debug.assert_called()

    def test_validate_image_url_accessible_request_exception(self, mock_requests_head, mock_logging):
        """Testa outras exceções de requisição."""
        # Arrange
        mock_requests_head.side_effect = requests.exceptions.RequestException("Network error")

        # Act
        result = ImageUrlValidator.validate_image_url_accessible('https://error.com/image.jpg')

        # Assert
        assert result is False
        mock_logging.debug.assert_called()

    def test_validate_image_url_accessible_custom_timeout(self, mock_requests_head):
        """Testa timeout customizado."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests_head.return_value = mock_response

        # Act
        ImageUrlValidator.validate_image_url_accessible('https://example.com/image.jpg', timeout=5)

        # Assert
        mock_requests_head.assert_called_once_with(
            'https://example.com/image.jpg',
            timeout=5,
            headers={'User-Agent': ImageUrlValidator.USER_AGENT},
            allow_redirects=True
        )

    @pytest.mark.parametrize("url", [
        None,
        "",
        "invalid-url",
        "ftp://example.com/image.jpg",  # scheme inválido para validação
        "//example.com/image.jpg",      # sem scheme
    ])
    def test_validate_image_url_accessible_invalid_urls(self, url, mock_logging):
        """Testa URLs inválidas."""
        # Act
        result = ImageUrlValidator.validate_image_url_accessible(url)

        # Assert
        assert result is False

    def test_validate_image_url_accessible_malformed_url(self, mock_logging):
        """Testa URL mal formada que causa erro no parsing."""
        # Act
        result = ImageUrlValidator.validate_image_url_accessible("http://[invalid-ipv6")

        # Assert
        assert result is False

    def test_validate_image_url_accessible_empty_string(self, mock_logging):
        """Testa string vazia."""
        # Act
        result = ImageUrlValidator.validate_image_url_accessible("")

        # Assert
        assert result is False
        mock_logging.debug.assert_called_with("URL de imagem vazia ou inválida")

    def test_validate_image_url_accessible_none_value(self, mock_logging):
        """Testa valor None."""
        # Act
        result = ImageUrlValidator.validate_image_url_accessible(None)

        # Assert
        assert result is False
        mock_logging.debug.assert_called_with("URL de imagem vazia ou inválida")

    def test_validate_image_url_accessible_non_string(self, mock_logging):
        """Testa valor que não é string."""
        # Act
        result = ImageUrlValidator.validate_image_url_accessible(123)

        # Assert
        assert result is False
        mock_logging.debug.assert_called_with("URL de imagem vazia ou inválida")

    @pytest.mark.parametrize("status_code,expected", [
        (200, True),
        (201, True),
        (202, True),
        (299, True),
        (300, False),
        (301, False),  # No mock, o redirect não é seguido, então o status é >= 300
        (302, False),  # No mock, o redirect não é seguido, então o status é >= 300
        (400, False),
        (401, False),
        (403, False),
        (404, False),
        (500, False),
    ])
    def test_validate_image_url_accessible_status_codes(self, mock_requests_head, status_code, expected):
        """Testa diferentes códigos de status HTTP."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_requests_head.return_value = mock_response
 
        # Act
        result = ImageUrlValidator.validate_image_url_accessible('https://example.com/image.jpg')
 
        # Assert
        assert result is expected

    def test_get_domain_success(self):
        """Testa extração bem-sucedida de domínio."""
        # Act & Assert
        assert ImageUrlValidator.get_domain('https://example.com/image.jpg') == 'example.com'
        assert ImageUrlValidator.get_domain('https://www.example.com/image.jpg') == 'example.com'
        assert ImageUrlValidator.get_domain('http://subdomain.example.com/path') == 'subdomain.example.com'

    def test_get_domain_invalid_urls(self):
        """Testa extração de domínio com URLs inválidas."""
        # Act & Assert
        assert ImageUrlValidator.get_domain(None) is None
        assert ImageUrlValidator.get_domain("") is None
        assert ImageUrlValidator.get_domain("invalid-url") == ""
        assert ImageUrlValidator.get_domain(123) is None

    def test_get_domain_case_insensitive(self):
        """Testa que o domínio é retornado em lowercase."""
        # Act & Assert
        assert ImageUrlValidator.get_domain('https://EXAMPLE.COM/image.jpg') == 'example.com'
        assert ImageUrlValidator.get_domain('https://WWW.EXAMPLE.COM/image.jpg') == 'example.com'