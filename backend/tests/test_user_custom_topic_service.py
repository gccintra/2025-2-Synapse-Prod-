import pytest
from unittest.mock import MagicMock, call
from app.services.user_custom_topic_service import UserCustomTopicService
from app.models.custom_topic import CustomTopic, CustomTopicValidationError
from sqlalchemy.exc import IntegrityError

@pytest.fixture
def mock_custom_topic_repository():
    return MagicMock()

@pytest.fixture
def mock_users_topics_repository():
    return MagicMock()

@pytest.fixture
def custom_topic_service(mock_custom_topic_repository, mock_users_topics_repository):
    return UserCustomTopicService(
        custom_topic_repo=mock_custom_topic_repository, 
        preferred_repo=mock_users_topics_repository
    )

def test_add_preferred_topic_new_topic(custom_topic_service, mock_custom_topic_repository, mock_users_topics_repository):
    user_id = 1
    topic_name = "Test Topic"
    new_topic = CustomTopic(id=1, name=topic_name.lower().strip())

    mock_users_topics_repository.count_by_user.return_value = 0
    mock_custom_topic_repository.find_by_name.return_value = None
    mock_custom_topic_repository.create.return_value = new_topic
    mock_users_topics_repository.attach.return_value = True

    result = custom_topic_service.add_preferred_topic(user_id, topic_name)
    
    assert result["topic"]['name'] == new_topic.name
    assert result["attached"] is True # type: ignore
    mock_custom_topic_repository.find_by_name.assert_called_once_with(topic_name.lower())
    mock_users_topics_repository.attach.assert_called_once_with(user_id, new_topic.id)

def test_add_preferred_topic_existing_topic(custom_topic_service, mock_custom_topic_repository, mock_users_topics_repository):
    user_id = 1
    topic_name = "Existing Topic"
    existing_topic = CustomTopic(id=10, name=topic_name.lower().strip())
    
    mock_users_topics_repository.count_by_user.return_value = 0
    mock_custom_topic_repository.find_by_name.return_value = existing_topic
    mock_users_topics_repository.attach.return_value = True
    
    result = custom_topic_service.add_preferred_topic(user_id, topic_name)
    
    assert result["topic"]['name'] == existing_topic.name
    assert result["attached"] is True # type: ignore
    mock_custom_topic_repository.find_by_name.assert_called_once_with(topic_name.lower()) 
    mock_custom_topic_repository.create.assert_not_called()
    mock_users_topics_repository.attach.assert_called_once_with(user_id, existing_topic.id)

def test_add_preferred_topic_already_attached(custom_topic_service, mock_custom_topic_repository, mock_users_topics_repository):
    user_id = 1
    topic_name = "Existing Topic"
    existing_topic = CustomTopic(id=10, name=topic_name.lower().strip())
    mock_users_topics_repository.count_by_user.return_value = 0
    mock_custom_topic_repository.find_by_name.return_value = existing_topic
    mock_users_topics_repository.attach.return_value = False # Simula que já estava associado

    result = custom_topic_service.add_preferred_topic(user_id, topic_name)
    
    assert result["topic"]['name'] == existing_topic.name
    assert result["attached"] is False # type: ignore
    mock_custom_topic_repository.find_by_name.assert_called_once_with(topic_name.lower())
    mock_custom_topic_repository.create.assert_not_called()
    mock_users_topics_repository.attach.assert_called_once_with(user_id, existing_topic.id)

def test_get_user_preferred_topics_returns_topics(custom_topic_service, mock_custom_topic_repository, mock_users_topics_repository):
    user_id = 1
    topic_ids = [1, 2, 3]
    topics = [
        CustomTopic(id=1, name="topic 1"),
        CustomTopic(id=2, name="topic 2"),
        CustomTopic(id=3, name="topic 3"),
    ]
    
    mock_users_topics_repository.list_user_topic_ids.return_value = topic_ids
    mock_custom_topic_repository.find_by_ids.return_value = topics
    
    result = custom_topic_service.get_user_preferred_topics(user_id)
    
    assert len(result) == 3
    assert [t['name'] for t in result] == ["topic 1", "topic 2", "topic 3"]
    mock_users_topics_repository.list_user_topic_ids.assert_called_once_with(user_id)
    mock_custom_topic_repository.find_by_ids.assert_called_once_with(topic_ids)

def test_remove_preferred_topic_successful(custom_topic_service, mock_users_topics_repository):
    user_id = 1
    topic_id = 10
    mock_users_topics_repository.detach.return_value = True

    result = custom_topic_service.remove_preferred_topic(user_id, topic_id)
    
    assert result is True
    mock_users_topics_repository.detach.assert_called_once_with(user_id, topic_id)

def test_remove_preferred_topic_not_found(custom_topic_service, mock_users_topics_repository):
    user_id = 1
    topic_id = 10
    mock_users_topics_repository.detach.return_value = False
    
    result = custom_topic_service.remove_preferred_topic(user_id, topic_id)
    
    assert result is False
    mock_users_topics_repository.detach.assert_called_once_with(user_id, topic_id)
    
def test_add_preferred_topic_raises_validation_error(custom_topic_service, mock_users_topics_repository):
    mock_users_topics_repository.count_by_user.return_value = 0
    with pytest.raises(CustomTopicValidationError, match="não pode ser vazio."):
        custom_topic_service.add_preferred_topic(user_id=1, name=" ")

def test_add_preferred_topic_integrity_error_and_fail_to_recover(custom_topic_service, mock_custom_topic_repository, mock_users_topics_repository):
    topic_name = "Unrecoverable Topic"

    mock_users_topics_repository.count_by_user.return_value = 0
    mock_custom_topic_repository.find_by_name.side_effect = [None, None]
    mock_custom_topic_repository.create.side_effect = IntegrityError(None, None, None)

    with pytest.raises(IntegrityError):
        custom_topic_service.add_preferred_topic(user_id=1, name=topic_name)

    assert mock_custom_topic_repository.find_by_name.call_count == 2