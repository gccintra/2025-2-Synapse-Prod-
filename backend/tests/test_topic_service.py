import pytest
from unittest.mock import MagicMock
from app.services.topic_service import TopicService
from app.models.topic import Topic

@pytest.fixture
def mock_topic_repository():
    return MagicMock()

@pytest.fixture
def topic_service(mock_topic_repository):
    return TopicService(topic_repo=mock_topic_repository)

def test_list_all_standard_topics(topic_service, mock_topic_repository):
    topics = [
        Topic(id=1, name="topic 1"),
        Topic(id=2, name="topic 2"),
        Topic(id=3, name="topic 3"),
    ]
    mock_topic_repository.list_all.return_value = topics
    result = topic_service.list_all_standard_topics()
    assert len(result) == 3
    assert [t.name for t in result] == ["topic 1", "topic 2", "topic 3"]
    mock_topic_repository.list_all.assert_called_once()
