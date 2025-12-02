import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager
from app.controllers.user_controller import UserController
from sqlalchemy.exc import IntegrityError
from app.models.exceptions import (
    UserValidationError,
    UserNotFoundError,
    EmailInUseError,
    InvalidPasswordError,
)

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

@pytest.fixture
def app_context():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "super-secret-test-key"
    JWTManager(app)
    with app.app_context():
        yield

@pytest.fixture
def mock_service():
    with patch('app.controllers.user_controller.UserService') as mock:
        yield mock.return_value

@pytest.fixture
def mock_google_service():
    with patch('app.controllers.user_controller.GoogleAuthService') as mock:
        yield mock.return_value

@pytest.fixture
def controller(mock_service, mock_google_service, app_context):
    controller = UserController()
    controller.service = mock_service
    controller.google_service = mock_google_service
    return controller

def test_register_success(controller, mock_service):
    data = {"full_name": "Test User", "email": "test@example.com", "password": "password123"}

    mock_user = MagicMock()
    mock_user.to_dict.return_value = {"id": 1, "email": data["email"], "full_name": data["full_name"]}
    mock_service.register.return_value = mock_user 

    response, status_code = controller.register(data)
    json_data = response.get_json()

    assert status_code == 201
    assert json_data["success"] is True
    assert json_data["message"] == "Usuário registrado com sucesso."
    assert json_data["data"] is None
    assert json_data["error"] is None

def test_register_key_error_returns_400(controller, mock_service):
    mock_service.register.side_effect = KeyError("full_name")
    response, status_code = controller.register({})
    json_data = response.get_json()

    assert status_code == 400
    assert "Campo obrigatório ausente" in json_data["error"]

def test_register_value_error_returns_400(controller, mock_service):
    mock_service.register.side_effect = ValueError("Email inválido.")
    data = {"full_name": "Test", "email": "invalid", "password": "123"}
    response, status_code = controller.register(data)
    json_data = response.get_json()

    assert status_code == 400
    assert "Email inválido." in json_data["error"]

def test_register_email_in_use_error_returns_409(controller, mock_service):
    mock_service.register.side_effect = EmailInUseError("E-mail já cadastrado")
    data = {"full_name": "Test", "email": "test@example.com", "password": "123"}
    response, status_code = controller.register(data)
    json_data = response.get_json()

    assert status_code == 409
    assert "E-mail já cadastrado" in json_data["error"]

def test_register_integrity_error_returns_409(controller, mock_service):
    mock_service.register.side_effect = IntegrityError("DB constraint", "params", "orig")
    data = {"full_name": "Test", "email": "test@example.com", "password": "123"}
    response, status_code = controller.register(data)
    json_data = response.get_json()

    assert status_code == 409
    assert "Erro de integridade" in json_data["message"]
    assert "O e-mail pode já estar em uso" in json_data["error"]

@patch('app.controllers.user_controller.logging')
def test_register_unexpected_exception_returns_500(mock_logging, controller, mock_service):
    mock_service.register.side_effect = Exception("Database is down")
    data = {"full_name": "Test", "email": "test@example.com", "password": "123"}
    response, status_code = controller.register(data)
    json_data = response.get_json()

    assert status_code == 500
    assert "Erro interno do servidor." in json_data["message"]

@patch('app.controllers.user_controller.create_access_token', return_value="dummy_token")
@patch('app.controllers.user_controller.set_access_cookies')
def test_login_successfully(mock_set_cookies, mock_create_token, controller, mock_service):
    user_obj = AttrDict({"id": 1, "full_name": "Test User", "email": "test@example.com"})
    mock_service.login.return_value = user_obj
    response, status_code = controller.login({"email": "test@example.com", "password": "password"})
    json_data = response.get_json()

    assert status_code == 200
    assert json_data["success"] is True
    mock_create_token.assert_called_once_with(identity='1')
    mock_set_cookies.assert_called_once()

def test_login_invalid_credentials_returns_401(controller, mock_service):
    mock_service.login.return_value = None
    response, status_code = controller.login({"email": "test@example.com", "password": "wrongpassword"})
    assert status_code == 401

def test_login_missing_fields_returns_400(controller, mock_service):
    mock_service.login.side_effect = KeyError("password")
    response, status_code = controller.login({"email": "test@example.com"})
    json_data = response.get_json()

    assert status_code == 400
    assert "Dados de login inválidos ou ausentes" in json_data["error"]

@patch('app.controllers.user_controller.logging')
def test_login_unexpected_exception_returns_500(mock_logging, controller, mock_service):
    mock_service.login.side_effect = Exception("DB connection error")
    response, status_code = controller.login({"email": "test@example.com", "password": "password"})
    assert status_code == 500

def test_get_profile_success(controller, mock_service):
    user_obj = AttrDict({
        "full_name": "Test User",
        "email": "test@example.com",
        "birthdate": MagicMock(isoformat=MagicMock(return_value="2000-01-01")),
        "newsletter": True
    })
    mock_service.get_profile.return_value = user_obj
    response, status_code = controller.get_profile(user_id=1)
    json_data = response.get_json()

    assert status_code == 200
    assert json_data["success"] is True
    assert json_data["data"]["full_name"] == "Test User"
    assert json_data["data"]["email"] == "test@example.com"
    assert json_data["data"]["birthdate"] == "2000-01-01"
    assert json_data["data"]["newsletter"] is True

@patch('app.controllers.user_controller.logging')
def test_get_profile_unexpected_exception_returns_500(mock_logging, controller, mock_service):
    mock_service.get_profile.side_effect = Exception("DB error")
    response, status_code = controller.get_profile(user_id=1)
    json_data = response.get_json()

    assert status_code == 500
    assert json_data["success"] is False
    assert "Erro interno do servidor" in json_data["message"]

def test_get_profile_user_not_found_returns_404(controller, mock_service):
    mock_service.get_profile.return_value = None
    response, status_code = controller.get_profile(user_id=999)
    assert status_code == 404

def test_update_profile_user_not_found_returns_404(controller, mock_service):
    mock_service.update_profile.side_effect = UserNotFoundError("Usuário não encontrado")
    response, status_code = controller.update_profile(user_id=999, data={})
    assert status_code == 404

def test_update_profile_success(controller, mock_service):
    updated_user = AttrDict({
        "full_name": "Updated Name",
        "email": "updated@example.com",
        "birthdate": None
    })
    mock_service.update_profile.return_value = updated_user
    response, status_code = controller.update_profile(user_id=1, data={"full_name": "Updated Name"})
    json_data = response.get_json()

    assert status_code == 200
    assert json_data["success"] is True
    assert "Perfil atualizado com sucesso" in json_data["message"]
    assert json_data["data"]["full_name"] == "Updated Name"
    assert json_data["data"]["email"] == "updated@example.com"
    assert json_data["data"]["birthdate"] is None

def test_update_profile_email_in_use_returns_409(controller, mock_service):
    mock_service.update_profile.side_effect = EmailInUseError("O novo e-mail já está em uso.")
    response, status_code = controller.update_profile(user_id=1, data={})
    assert status_code == 409

def test_update_profile_validation_error_returns_400(controller, mock_service):
    mock_service.update_profile.side_effect = ValueError("Formato de email inválido.")
    response, status_code = controller.update_profile(user_id=1, data={})
    assert status_code == 400

@patch('app.controllers.user_controller.logging')
def test_update_profile_unexpected_exception_returns_500(mock_logging, controller, mock_service):
    mock_service.update_profile.side_effect = Exception("DB error")
    response, status_code = controller.update_profile(user_id=1, data={})
    json_data = response.get_json()

    assert status_code == 500
    assert json_data["success"] is False
    assert "Erro interno do servidor" in json_data["message"]

def test_update_password_success(controller, mock_service):
    mock_service.change_password.return_value = None
    response, status_code = controller.update_password(user_id=1, data={"new_password": "new_password"})
    assert status_code == 200
    assert response.get_json()["success"] is True

def test_update_password_user_not_found_returns_404(controller, mock_service):
    mock_service.change_password.side_effect = UserNotFoundError("Usuário não encontrado.")
    response, status_code = controller.update_password(user_id=999, data={})
    assert status_code == 404

def test_update_password_validation_error_returns_400(controller, mock_service):
    mock_service.change_password.side_effect = ValueError("A senha deve ter no mínimo 8 caracteres.")
    response, status_code = controller.update_password(user_id=1, data={})
    assert status_code == 400

@patch('app.controllers.user_controller.logging')
def test_update_password_unexpected_exception_returns_500(mock_logging, controller, mock_service):
    mock_service.change_password.side_effect = Exception("DB error")
    response, status_code = controller.update_password(user_id=1, data={})
    json_data = response.get_json()

    assert status_code == 500
    assert "Erro interno do servidor" in json_data["message"]

@patch('app.controllers.user_controller.unset_jwt_cookies')
def test_logout_sucessfully(mock_unset_cookies, controller):
    user_id = 1
    response, status_code = controller.logout(user_id)
    json_data = response.get_json()

    assert status_code == 200
    assert json_data["success"] is True
    assert "Logout bem-sucedido" in json_data["message"]
    mock_unset_cookies.assert_called_once_with(response)

@patch('app.controllers.user_controller.logging')
def test_logout_unexpected_exception_returns_500(mock_logging, controller):
    with patch('app.controllers.user_controller.unset_jwt_cookies', side_effect=Exception("Cookie error")):
        response, status_code = controller.logout(user_id=1)
        json_data = response.get_json()

        assert status_code == 500
        assert "Erro interno do servidor" in json_data["message"]

def test_update_newsletter_success(controller, mock_service):
    mock_service.update_newsletter.return_value = None
    response, status_code = controller.update_newsletter(user_id=1, data={"value": True})
    json_data = response.get_json()

    assert status_code == 200
    assert json_data["success"] is True
    assert "Preferência de newsletter atualizada com sucesso" in json_data["message"]

def test_update_newsletter_user_not_found_returns_404(controller, mock_service):
    mock_service.update_newsletter.side_effect = UserNotFoundError("Usuário não encontrado")
    response, status_code = controller.update_newsletter(user_id=999, data={"value": True})
    assert status_code == 404

def test_update_newsletter_value_error_returns_400(controller, mock_service):
    mock_service.update_newsletter.side_effect = ValueError("Valor inválido")
    response, status_code = controller.update_newsletter(user_id=1, data={"value": "invalid"})
    assert status_code == 400

def test_update_newsletter_no_data_returns_400(controller):
    response, status_code = controller.update_newsletter(user_id=1, data=None)
    json_data = response.get_json()
    assert status_code == 400
    assert "Erro ao receber os dados da requisição" in json_data["error"]

@patch('app.controllers.user_controller.logging')
def test_update_newsletter_unexpected_exception_returns_500(mock_logging, controller, mock_service):
    mock_service.update_newsletter.side_effect = Exception("DB error")
    response, status_code = controller.update_newsletter(user_id=1, data={"value": True})
    assert status_code == 500

@patch('app.controllers.user_controller.create_access_token', return_value="dummy_google_token")
@patch('app.controllers.user_controller.set_access_cookies')
def test_google_login_success(mock_set_cookies, mock_create_token, controller, mock_google_service):
    user_obj = AttrDict({"id": 2, "full_name": "Google User", "email": "google@example.com"})
    mock_google_service.google_login.return_value = user_obj
    
    response, status_code = controller.google_login({"id_token": "valid_token"})
    json_data = response.get_json()

    assert status_code == 200
    assert json_data["success"] is True
    assert "Login com Google bem-sucedido" in json_data["message"]
    assert json_data["data"]["full_name"] == "Google User"
    mock_google_service.google_login.assert_called_once_with("valid_token")
    mock_create_token.assert_called_once_with(identity='2')
    mock_set_cookies.assert_called_once()

def test_google_login_missing_token_returns_400(controller):
    response, status_code = controller.google_login({})
    json_data = response.get_json()

    assert status_code == 400
    assert "Campo obrigatório ausente" in json_data["error"]

def test_google_login_invalid_token_returns_401(controller, mock_google_service):
    mock_google_service.google_login.side_effect = ValueError("Token inválido")
    response, status_code = controller.google_login({"id_token": "invalid_token"})
    json_data = response.get_json()

    assert status_code == 401
    assert "Falha na autenticação do Google" in json_data["message"]
    assert "Token inválido" in json_data["error"]

def test_google_login_email_in_use_returns_409(controller, mock_google_service):
    mock_google_service.google_login.side_effect = EmailInUseError("E-mail já cadastrado com outro método")
    response, status_code = controller.google_login({"id_token": "valid_token"})
    json_data = response.get_json()

    assert status_code == 409
    assert "Conflito de dados" in json_data["message"]
    assert "E-mail já cadastrado" in json_data["error"]

@patch('app.controllers.user_controller.logging')
def test_google_login_unexpected_exception_returns_500(mock_logging, controller, mock_google_service):
    mock_google_service.google_login.side_effect = Exception("Google API down")
    response, status_code = controller.google_login({"id_token": "any_token"})
    json_data = response.get_json()

    assert status_code == 500
    assert "Erro interno do servidor" in json_data["message"]
