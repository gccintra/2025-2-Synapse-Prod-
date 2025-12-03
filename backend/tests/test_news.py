import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models.news import News
from app.models.exceptions import NewsValidationError

# Mock da entidade ORM para isolar os testes do modelo
NewsEntity = MagicMock()


@pytest.fixture
def valid_news_data():
    """Fixture que fornece dados válidos para criar uma instância de News."""
    return {
        "title": "  Test Title with extra spaces  ",
        "url": "http://example.com/news",
        "published_at": datetime.now(),
        "source_id": 1,
        "content": "This is the news content.",
        "html": "<p>This is the news content.</p>",
        "topic_id": 2,
        "id": 100,
        "description": "A test description.",
        "image_url": "http://example.com/image.png",
        "created_at": datetime.now(),
        "source_name": "Example Source",
        "topic_name": "Technology",
    }


def test_news_creation_with_valid_data(valid_news_data):
    news = News(**valid_news_data)

    assert news.id == valid_news_data["id"]
    assert news.title == "Test Title with extra spaces"  # Título deve ser normalizado
    assert news.url == valid_news_data["url"]
    assert news.html == valid_news_data["html"]
    assert news.published_at == valid_news_data["published_at"]
    assert news.source_id == valid_news_data["source_id"]
    assert news.content == valid_news_data["content"]
    assert news.topic_id == valid_news_data["topic_id"]
    assert news.description == valid_news_data["description"]
    assert news.image_url == valid_news_data["image_url"]
    assert news.created_at == valid_news_data["created_at"]
    assert news.source_name == valid_news_data["source_name"]
    assert news.topic_name == valid_news_data["topic_name"]


@pytest.mark.parametrize("invalid_title", [None, "", "   ", 123])
def test_title_validation_raises_error(valid_news_data, invalid_title):
    with pytest.raises(NewsValidationError, match="title.*não pode ser vazio"):
        valid_news_data["title"] = invalid_title
        News(**valid_news_data)


@pytest.mark.parametrize("invalid_url, error_msg", [
    (None, "não pode ser vazia"),
    ("", "não pode ser vazia"),
    ("a" * 501, "tamanho inválido"),
    ("not-a-url", "formato inválido"),
    ("http:/invalid.com", "formato inválido"),
    (123, "não pode ser vazia"),
])
def test_url_validation_raises_error(valid_news_data, invalid_url, error_msg):
    with pytest.raises(NewsValidationError, match=f"url.*{error_msg}"):
        valid_news_data["url"] = invalid_url
        News(**valid_news_data)


def test_image_url_can_be_none(valid_news_data):
    valid_news_data["image_url"] = None
    news = News(**valid_news_data)
    assert news.image_url is None


@pytest.mark.parametrize("invalid_image_url, error_msg", [
    ("a" * 501, "formato ou tamanho inválido"),
    ("not-a-url", "formato ou tamanho inválido"),
])
def test_image_url_validation_raises_error(valid_news_data, invalid_image_url, error_msg):
    with pytest.raises(NewsValidationError, match=f"image_url.*{error_msg}"):
        valid_news_data["image_url"] = invalid_image_url
        News(**valid_news_data)


@pytest.mark.parametrize("invalid_published_at", [None, "not-a-date", 123])
def test_published_at_validation_raises_error(valid_news_data, invalid_published_at):
    with pytest.raises(NewsValidationError, match="published_at.*deve ser um datetime válido"):
        valid_news_data["published_at"] = invalid_published_at
        News(**valid_news_data)


@pytest.mark.parametrize("invalid_id", [None, 0, -1, "a", 1.5])
def test_source_id_validation_raises_error(valid_news_data, invalid_id):

    with pytest.raises(NewsValidationError, match="source_id.*deve ser um inteiro positivo"):
        valid_news_data["source_id"] = invalid_id
        News(**valid_news_data)


@pytest.mark.parametrize("invalid_id", [None, 0, -1, "a", 1.5])
def test_topic_id_validation_raises_error(valid_news_data, invalid_id):

    with pytest.raises(NewsValidationError, match="topic_id.*deve ser um inteiro positivo"):
        valid_news_data["topic_id"] = invalid_id
        News(**valid_news_data)


@pytest.fixture
def mock_news_entity():
    """Fixture que cria um mock de NewsEntity com relacionamentos."""
    entity = MagicMock()
    entity.id = 1
    entity.title = "Entity Title"
    entity.description = "Entity Description"
    entity.url = "http://entity.com"
    entity.image_url = "http://entity.com/image.jpg"
    entity.content = "Entity content."
    entity.html = "<p>Entity content.</p>"
    entity.published_at = datetime.now()
    entity.source_id = 10
    entity.topic_id = 20
    entity.created_at = datetime.now()

    # Simula relacionamentos
    entity.source = MagicMock()
    entity.source.name = "Entity Source Name"
    entity.topic = MagicMock()
    entity.topic.name = "Entity Topic Name"

    return entity


def test_from_entity_with_full_data(mock_news_entity):
    news = News.from_entity(mock_news_entity)

    assert news.id == mock_news_entity.id
    assert news.title == mock_news_entity.title
    assert news.source_name == "Entity Source Name"
    assert news.topic_name == "Entity Topic Name"
    assert news.url == mock_news_entity.url


def test_from_entity_with_missing_relations(mock_news_entity):

    mock_news_entity.source = None
    mock_news_entity.topic = None

    news = News.from_entity(mock_news_entity)

    assert news.source_name is None
    assert news.topic_name is None


def test_from_entity_with_none_entity():
    assert News.from_entity(None) is None


def test_to_orm(valid_news_data):
    with patch('app.models.news.NewsEntity') as MockNewsEntity:
        news = News(**valid_news_data)
        orm_entity = news.to_orm()

        # Verifica se o construtor da entidade mockada foi chamado com os argumentos corretos
        MockNewsEntity.assert_called_once_with(
            id=news.id,
            title=news.title,
            description=news.description,
            url=news.url,
            image_url=news.image_url,
            content=news.content,
            html=news.html,
            published_at=news.published_at,
            source_id=news.source_id,
            topic_id=news.topic_id,
            created_at=news.created_at,
        )

        # O retorno de to_orm() deve ser a instância criada pelo construtor mockado
        assert orm_entity == MockNewsEntity.return_value