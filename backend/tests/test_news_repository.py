import unittest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.news_repository import NewsRepository
from app.models.news import News

try:
    from app.entities.news_entity import NewsEntity
    from app.entities.news_source_entity import NewsSourceEntity
    from app.entities.user_saved_news_entity import UserSavedNewsEntity
    from app.entities.user_entity import UserEntity
    from app.entities.user_read_history_entity import UserReadHistoryEntity 
except ImportError:
    pass


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def news_repository(mock_session):
    return NewsRepository(session=mock_session)


@pytest.fixture
def sample_news_model():
    return News(
        id=1,
        title="Test News",
        url="http://www.example.com/news/1",
        content="This is a test.",
        published_at=datetime.now(),
        source_id=1,
        topic_id=1
    )


@pytest.fixture
def sample_news_entity():
    mock_entity = MagicMock()
    mock_entity.id = 1
    mock_entity.title = "Test News"
    mock_entity.url = "http://www.example.com/news/1"
    mock_entity.content = "This is a test."
    mock_entity.published_at = datetime.now()
    mock_entity.image_url = "http://example.com/image.jpg"
    mock_entity.source_id = 1
    mock_entity.topic_id = 1
    mock_entity.source = MagicMock(id=1, name="Test Source")
    return mock_entity


def test_create_news_success(news_repository, mock_session, sample_news_model, sample_news_entity):
    mock_session.add.return_value = None
    mock_session.commit.return_value = None

    sample_news_model.to_orm = MagicMock(return_value=sample_news_entity)

    def refresh_side_effect(entity):
        entity.id = 1
    mock_session.refresh.side_effect = refresh_side_effect
    
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        created_news = news_repository.create(sample_news_model)

    mock_session.add.assert_called_once_with(ANY)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert created_news is not None
    assert created_news.title == sample_news_model.title


def test_create_news_sqlalchemy_error(news_repository, mock_session, sample_news_model, sample_news_entity):
    sample_news_model.to_orm = MagicMock(return_value=sample_news_entity)

    mock_session.add.return_value = None
    mock_session.commit.side_effect = SQLAlchemyError("Simulated DB error")

    with pytest.raises(SQLAlchemyError):
        news_repository.create(sample_news_model)

    mock_session.add.assert_called_once_with(ANY)
    mock_session.rollback.assert_called_once()


def test_find_by_id_found(news_repository, mock_session, sample_news_entity, sample_news_model):
    mock_result = MagicMock()
    mock_result.first.return_value = (sample_news_entity, False)
    mock_session.execute.return_value = mock_result
    
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        found_news = news_repository.find_by_id(1, user_id=10)

    mock_session.execute.assert_called_once()
    assert found_news is not None
    assert found_news.id == sample_news_model.id
    assert found_news.is_favorited is False


def test_find_by_id_not_found(news_repository, mock_session):
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.execute.return_value = mock_result

    found_news = news_repository.find_by_id(999)

    mock_session.execute.assert_called_once()
    assert found_news is None


def test_find_by_id_sqlalchemy_error(news_repository, mock_session):
    mock_session.execute.side_effect = SQLAlchemyError("Simulated DB error")

    with pytest.raises(SQLAlchemyError):
        news_repository.find_by_id(1)

    mock_session.commit.assert_not_called()
    mock_session.rollback.assert_not_called()


@pytest.mark.parametrize("url, expected", [
    ("http://www.example.com/path/", "http://example.com/path"),
    ("https://example.com/path", "https://example.com/path"),
    ("http://example.com/path?query=1", "http://example.com/path"),
    ("HTTP://EXAMPLE.COM/PATH/", "http://example.com/path"),
    ("  http://www.example.com/path/  ", "http://example.com/path"),
    (None, None),
    ("", ""),
])
def test_normalize_url(news_repository, url, expected):
    assert news_repository._normalize_url(url) == expected


def test_normalize_url_with_malformed_url(news_repository):
    malformed_url = "http://[::1]/"
    assert news_repository._normalize_url(malformed_url) == "http://[::1]"


def test_find_by_url_normalized(news_repository, mock_session, sample_news_entity, sample_news_model):
    mock_session.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=sample_news_entity))
    ]
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        found_news = news_repository.find_by_url("http://www.example.com/news/1/")

    assert mock_session.execute.call_count == 2
    assert found_news is not None
    assert found_news.id == sample_news_model.id


def test_find_by_url_iterating(news_repository, mock_session, sample_news_entity, sample_news_model):
    mock_session.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[sample_news_entity]))))
    ]
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        found_news = news_repository.find_by_url("http://example.com/news/1?param=true")

    assert mock_session.execute.call_count == 3
    assert found_news is not None
    assert found_news.id == sample_news_model.id


def test_find_by_url_not_found(news_repository, mock_session):
    mock_session.execute.return_value.scalar_one_or_none.return_value = None
    mock_session.execute.return_value.scalars.return_value.all.return_value = []

    # Act
    found_news = news_repository.find_by_url("http://nonexistent.com")

    assert found_news is None


def test_find_by_url_exact_match(news_repository, mock_session, sample_news_entity, sample_news_model):
    mock_session.execute.return_value.scalar_one_or_none.return_value = sample_news_entity
    
    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        found_news = news_repository.find_by_url("http://www.example.com/news/1")

    mock_session.execute.assert_called_once()
    assert found_news is not None
    assert found_news.id == sample_news_model.id


def test_list_all(news_repository, mock_session, sample_news_entity, sample_news_model):
    mock_result = MagicMock()
    mock_result.all.return_value = [(sample_news_entity, True)]
    mock_session.execute.return_value = mock_result

    with patch('app.models.news.News.from_entity', return_value=sample_news_model) as mock_from_entity:
        news_list = news_repository.list_all(page=1, per_page=10, user_id=10)

    mock_session.execute.assert_called_once()
    mock_from_entity.assert_called_once_with(sample_news_entity)
    assert len(news_list) == 1
    assert news_list[0].id == sample_news_model.id
    assert news_list[0].is_favorited is True


def test_list_all_without_user_id(news_repository, mock_session, sample_news_entity, sample_news_model):
    mock_result = MagicMock()
    mock_result.all.return_value = [(sample_news_entity, False)]
    mock_session.execute.return_value = mock_result

    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        news_list = news_repository.list_all(page=1, per_page=10, user_id=None)

    mock_session.execute.assert_called_once()
    assert len(news_list) == 1
    assert news_list[0].is_favorited is False


def test_list_all_empty(news_repository, mock_session):
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    news_list = news_repository.list_all()

    mock_session.execute.assert_called_once()
    assert news_list == []


def test_list_all_sqlalchemy_error(news_repository, mock_session):
    mock_session.execute.side_effect = SQLAlchemyError("Simulated DB error")
    with pytest.raises(SQLAlchemyError):
        news_repository.list_all()


def test_find_by_topic(news_repository, mock_session, sample_news_entity, sample_news_model):
    mock_result = MagicMock()
    mock_result.all.return_value = [(sample_news_entity, False)]
    mock_session.execute.return_value = mock_result

    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        news_list = news_repository.find_by_topic(topic_id=1, user_id=10)

    mock_session.execute.assert_called_once()
    assert len(news_list) == 1
    assert news_list[0].topic_id == sample_news_model.topic_id


def test_find_by_topic_empty(news_repository, mock_session):
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    news_list = news_repository.find_by_topic(topic_id=99, user_id=10)

    mock_session.execute.assert_called_once()
    assert news_list == []


def test_count_all(news_repository, mock_session):
    mock_session.execute.return_value.scalar.return_value = 150

    count = news_repository.count_all()

    assert count == 150
    mock_session.execute.assert_called_once()


def test_count_all_sqlalchemy_error(news_repository, mock_session):
    mock_session.execute.side_effect = SQLAlchemyError("Simulated DB error")
    with pytest.raises(SQLAlchemyError):
        news_repository.count_all()


def test_count_by_topic(news_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalar.return_value = 5
    mock_session.execute.return_value = mock_result

    count = news_repository.count_by_topic(topic_id=1)

    mock_session.execute.assert_called_once()
    assert count == 5


def test_count_by_topic_sqlalchemy_error(news_repository, mock_session):
    mock_session.execute.side_effect = SQLAlchemyError("Simulated DB error")
    with pytest.raises(SQLAlchemyError):
        news_repository.count_by_topic(topic_id=1)


def test_list_favorites_by_user(news_repository, mock_session, sample_news_entity, sample_news_model):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_news_entity]
    mock_session.execute.return_value = mock_result

    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        news_list = news_repository.list_favorites_by_user(user_id=10)

    mock_session.execute.assert_called_once()
    assert len(news_list) == 1
    assert news_list[0].id == sample_news_model.id


def test_list_favorites_by_user_empty(news_repository, mock_session):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    news_list = news_repository.list_favorites_by_user(user_id=10)

    mock_session.execute.assert_called_once()
    assert news_list == []


def test_get_recent_news_with_base_score(news_repository, mock_session, sample_news_entity, sample_news_model):
    sample_news_entity.published_at = datetime.now() - timedelta(hours=12)
    
    result_row = (sample_news_entity, 300, 100, True)
    
    mock_result = MagicMock()
    mock_result.all.return_value = [result_row]
    mock_session.execute.return_value = mock_result

    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        news_list = news_repository.get_recent_news_with_base_score(
            user_id=10, 
            preferred_source_ids=[1], 
            days_limit=15
        )

    mock_session.execute.assert_called_once()
    assert len(news_list) == 1
    
    scored_news = news_list[0]
    assert scored_news.id == sample_news_model.id
    assert scored_news.is_favorited is True
    assert scored_news.time_score == 300
    assert scored_news.source_score == 100


def test_get_recent_news_with_base_score_no_preferred_source(news_repository, mock_session, sample_news_entity, sample_news_model):
    sample_news_entity.published_at = datetime.now() - timedelta(days=3)
    
    result_row = (sample_news_entity, 75, 0, False)
    
    mock_result = MagicMock()
    mock_result.all.return_value = [result_row]
    mock_session.execute.return_value = mock_result

    with patch('app.models.news.News.from_entity', return_value=sample_news_model):
        news_list = news_repository.get_recent_news_with_base_score(
            user_id=10, 
            preferred_source_ids=[99],
            days_limit=15
        )

    mock_session.execute.assert_called_once()
    assert len(news_list) == 1
    
    scored_news = news_list[0]
    assert scored_news.id == sample_news_model.id
    assert scored_news.is_favorited is False
    assert scored_news.time_score == 75
    assert scored_news.source_score == 0


def test_get_recent_news_with_base_score_empty(news_repository, mock_session):
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    news_list = news_repository.get_recent_news_with_base_score(user_id=10, preferred_source_ids=[], days_limit=5)

    mock_session.execute.assert_called_once()
    assert news_list == []


def test_get_recent_news_with_base_score_sqlalchemy_error(news_repository, mock_session):
    mock_session.execute.side_effect = SQLAlchemyError("Simulated DB error")

    with pytest.raises(SQLAlchemyError):
        news_repository.get_recent_news_with_base_score(user_id=10, preferred_source_ids=[], days_limit=5)