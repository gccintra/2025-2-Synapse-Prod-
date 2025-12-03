import pytest
from unittest.mock import patch, MagicMock
from app.controllers.topic_controller import TopicController
from app.models.exceptions import CustomTopicValidationError
from sqlalchemy.exc import IntegrityError
from flask import Flask

@pytest.fixture
def mock_service():
    # O controlador instancia UserCustomTopicService, então mockamos esse
    with patch('app.controllers.topic_controller.UserCustomTopicService') as mock:
        yield mock.return_value

@pytest.fixture
def app_context():
    app = Flask(__name__)
    with app.app_context():
        yield app

@pytest.fixture
def topic_controller(mock_service, app_context):
    controller = TopicController()
    controller.custom_topic_service = mock_service
    return controller

def test_create_topic_validation_error_returns_400(topic_controller, mock_service, app_context):
    user_id = 1
    data = {}
    # Simula um contexto de requisição com um corpo JSON
    with app_context.test_request_context(json=data):
        # O controller lança CustomTopicValidationError internamente, mas o método em si
        # retorna um JSON de erro 400 quando o payload não tem 'name'.
        # Não precisamos mockar o side_effect aqui para este caso específico.

        response, status_code = topic_controller.add_preferred_topic(user_id)

    assert status_code == 400
    assert response.json['success'] is False
    assert "Campo 'name' é obrigatório." in response.json['message']
    assert "Dados inválidos" in response.json['error']

def test_create_topic_integrity_error_returns_500(topic_controller, mock_service, app_context):
    user_id = 1
    data = {"name": "existing_topic"}
    # Simula um contexto de requisição com um corpo JSON
    with app_context.test_request_context(json=data):
        mock_service.add_preferred_topic.side_effect = IntegrityError("Integrity Error", None, None)

        response, status_code = topic_controller.add_preferred_topic(user_id)

    assert status_code == 500
    assert response.json['success'] is False
    assert "Erro interno ao criar tópico." in response.json['message']
    mock_service.add_preferred_topic.assert_called_once_with(user_id, data['name'])
    
@patch('app.controllers.topic_controller.logging')
def test_create_topic_unexpected_exception_returns_500(mock_logging, topic_controller, mock_service, app_context):
    user_id = 1
    data = {"name": "test"}
    with app_context.test_request_context(json=data):
        mock_service.add_preferred_topic.side_effect = Exception("An unexpected error occurred.")
        
        response, status_code = topic_controller.add_preferred_topic(user_id)
    
    assert status_code == 500
    assert response.json['success'] is False
    assert "Erro interno ao criar tópico." in response.json['message']

def test_find_by_user_successful_returns_200(topic_controller, mock_service):
    user_id = 1
    topics = [
        {"id": 1, "name": "topic1"},
        {"id": 2, "name": "topic2"}
    ]
    statistics = {"total": 2}
    mock_service.get_user_preferred_topics.return_value = topics
    mock_service.get_user_statistics.return_value = statistics
    
    response, status_code = topic_controller.list_user_preferred_topics(user_id)
    
    assert status_code == 200
    assert response.json['success'] is True
    assert len(response.json['data']['topics']) == 2
    assert response.json['data']['topics'][0]['name'] == 'topic1'
    assert response.json['data']['statistics']['total'] == 2
    mock_service.get_user_preferred_topics.assert_called_once_with(user_id)
    mock_service.get_user_statistics.assert_called_once_with(user_id)
    
@patch('app.controllers.topic_controller.logging')
def test_find_by_user_with_exception_returns_500(mock_logging, topic_controller, mock_service):
    user_id = 1
    mock_service.get_user_preferred_topics.side_effect = Exception("DB error")
    
    response, status_code = topic_controller.list_user_preferred_topics(user_id)
    
    assert status_code == 500
    assert response.json['success'] is False
    assert "Erro interno ao buscar tópicos." in response.json['message']
    
def test_detach_my_topic_successful_returns_200(topic_controller, mock_service):
    user_id = 1
    topic_id = 1
    mock_service.remove_preferred_topic.return_value = True
    
    response, status_code = topic_controller.remove_preferred_topic(user_id, topic_id)
    
    assert status_code == 200
    assert response.json['success'] is True
    assert "Tópico removido das preferências com sucesso." in response.json['message']
    mock_service.remove_preferred_topic.assert_called_once_with(user_id, topic_id)

def test_detach_my_topic_not_found_returns_404(topic_controller, mock_service):
    user_id = 1
    topic_id = 999
    mock_service.remove_preferred_topic.return_value = False
    
    response, status_code = topic_controller.remove_preferred_topic(user_id, topic_id)
    
    assert status_code == 404
    assert response.json['success'] is False
    assert "Tópico não encontrado." in response.json['message']
    assert "Not Found" in response.json['error']
    mock_service.remove_preferred_topic.assert_called_once_with(user_id, topic_id)

@patch('app.controllers.topic_controller.logging')
def test_detach_my_topic_with_exception_returns_500(mock_logging, topic_controller, mock_service):
    user_id = 1
    topic_id = 1
    mock_service.remove_preferred_topic.side_effect = Exception("DB error")
    
    response, status_code = topic_controller.remove_preferred_topic(user_id, topic_id)
    
    assert status_code == 500
    assert response.json['success'] is False
    assert "Erro interno ao remover tópico." in response.json['message']