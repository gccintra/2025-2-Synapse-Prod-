import pytest
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.models.exceptions import (
    InvalidPasswordError,
    UserNotFoundError,
    NewsNotFoundError,
    NewsAlreadyFavoritedError,
    NewsNotFavoritedError
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import date
from unittest.mock import patch, MagicMock
from app.entities.user_entity import UserEntity
from app.entities.news_entity import NewsEntity

@pytest.fixture
def user_repository(db):
    return UserRepository(session=db.session)

def test_create_user_successfully(user_repository):
    user_model = User(
        full_name="New User",
        email="new.user@example.com",
        password="ValidPassword123",
        birthdate=date(2000,1,1),
    )
    created_user = user_repository.create(user_model)
    assert created_user.id is not None
    assert created_user.email == user_model.email.lower()
    assert created_user.full_name == user_model.full_name

def test_create_user_with_duplicate_email_fails(user_repository):
    user_repository.create(User(full_name="user One", email="test@example.com", password="Password123"))
    
    with pytest.raises(IntegrityError):
        user_repository.create(User(full_name="User Two", email="test@example.com", password="Password456"))
        
        
def test_find_by_email_case_insensitive(user_repository):
    user_repository.create(User(full_name="Test User", email="test.user@example.com", password="Password123"))
    
    found_user = user_repository.find_by_email("TEST.USER@example.com")
    
    assert found_user is not None
    assert found_user.full_name == "Test User"
    
def test_find_by_email_not_found(user_repository):
    found_user = user_repository.find_by_email("non-existent@example.com")
    assert found_user is None
    

def test_find_by_id_successfully(user_repository):
    created_user = user_repository.create(User(full_name="Find Me", email="find.me@example.com", password="Password123"))
    
    found_user = user_repository.find_by_id(created_user.id)
    
    assert found_user is not None
    assert found_user.id == created_user.id

def test_find_by_id_not_found(user_repository):
    found_user = user_repository.find_by_id(999)
    assert found_user is None
    
def test_update_user_successfully(user_repository):
    user = user_repository.create(User(full_name="Old Name", email="update.me@example.com", password="Password123"))
    
    user.full_name = "New Name"
    updated_user = user_repository.update(user)
    
    assert updated_user.full_name == "New Name"
    assert updated_user.email == "update.me@example.com"
def test_update_user_without_id_raises_error(user_repository):
    user_model = User(full_name="No ID", email="noid@example.com", password="ValidPassword123", id=None)
    
    with pytest.raises(ValueError) as e:
        user_repository.update(user_model)
    
    assert "O modelo de usuário deve ter um ID para ser atualizado." in str(e.value)


def test_create_user_sqlalchemy_error_raises_exception(user_repository, db):
    user_model = User(full_name="New User", email="new.user.error@example.com", password="ValidPassword123")
    
    with patch.object(db.session, 'commit', side_effect=SQLAlchemyError("Simulated DB Error")):
        with pytest.raises(SQLAlchemyError):
            user_repository.create(user_model)

    with patch.object(db.session, 'rollback') as mock_rollback:
        with patch.object(db.session, 'commit', side_effect=SQLAlchemyError("Simulated DB Error")):
            with pytest.raises(SQLAlchemyError):
                user_repository.create(user_model)
        mock_rollback.assert_called_once()
        
def test_update_user_sqlalchemy_error_raises_exception(user_repository, db):
    user = user_repository.create(User(full_name="Old Name", email="update.me.error@example.com", password="ValidPassword123"))
    user.full_name = "New Name"
    
    with patch.object(db.session, 'commit', side_effect=SQLAlchemyError("Simulated DB Error")):
        with pytest.raises(SQLAlchemyError):
            user_repository.update(user)

    with patch.object(db.session, 'rollback') as mock_rollback:
        with patch.object(db.session, 'commit', side_effect=SQLAlchemyError("Simulated DB Error")):
            with pytest.raises(SQLAlchemyError):
                user_repository.update(user)
        mock_rollback.assert_called_once()

def test_list_all_returns_list_of_users(user_repository):
    
    user_repository.create(User(full_name="User One", email="user1@example.com", password="Password123"))
    user_repository.create(User(full_name="User Two", email="user2@example.com", password="Password123"))

    users = user_repository.list_all()

    assert isinstance(users, list)
    assert len(users) == 2
    assert all(isinstance(u, User) for u in users)

def test_list_all_returns_empty_list_when_no_users(user_repository):

    users = user_repository.list_all()
    assert users == []

def test_add_favorite_news_success(user_repository, db):

    user_entity = UserEntity(id=1, full_name="Test", email="test@test.com", password_hash="hash")
    news_entity = NewsEntity(id=10, title="News", url="http://news.com")
    user_entity.saved_news = [] # Garante que a lista de favoritos está vazia

    with patch.object(db.session, 'get') as mock_get, \
         patch.object(db.session, 'commit') as mock_commit:
        mock_get.side_effect = [user_entity, news_entity]
        user_repository.add_favorite_news(user_id=1, news_id=10)

    assert news_entity in user_entity.saved_news
    mock_commit.assert_called_once()

def test_add_favorite_news_user_not_found(user_repository, db):
    
    with patch.object(db.session, 'get', return_value=None):
        with pytest.raises(UserNotFoundError):
            user_repository.add_favorite_news(user_id=999, news_id=10)

def test_add_favorite_news_news_not_found(user_repository, db):
    
    user_entity = UserEntity(id=1, full_name="Test", email="test@test.com", password_hash="hash")
    with patch.object(db.session, 'get') as mock_get:
        mock_get.side_effect = [user_entity, None]
        with pytest.raises(NewsNotFoundError):
            user_repository.add_favorite_news(user_id=1, news_id=999)

def test_add_favorite_news_already_favorited(user_repository, db):

    user_entity = UserEntity(id=1, full_name="Test", email="test@test.com", password_hash="hash")
    news_entity = NewsEntity(id=10, title="News", url="http://news.com")
    user_entity.saved_news = [news_entity] # Notícia já está na lista

    with patch.object(db.session, 'get') as mock_get:
        mock_get.side_effect = [user_entity, news_entity]
        with pytest.raises(NewsAlreadyFavoritedError):
            user_repository.add_favorite_news(user_id=1, news_id=10)

def test_add_favorite_news_sqlalchemy_error(user_repository, db):

    user_entity = UserEntity(id=1, full_name="Test", email="test@test.com", password_hash="hash")
    news_entity = NewsEntity(id=10, title="News", url="http://news.com")
    user_entity.saved_news = []

    with patch.object(db.session, 'get') as mock_get:
        with patch.object(db.session, 'commit', side_effect=SQLAlchemyError("DB Error")) as mock_commit, \
             patch.object(db.session, 'rollback') as mock_rollback:
            mock_get.side_effect = [user_entity, news_entity]
            with pytest.raises(SQLAlchemyError):
                user_repository.add_favorite_news(user_id=1, news_id=10)
            mock_rollback.assert_called_once()

def test_remove_favorite_news_success(user_repository, db):

    user_entity = UserEntity(id=1, full_name="Test", email="test@test.com", password_hash="hash")
    news_entity = NewsEntity(id=10, title="News", url="http://news.com")
    user_entity.saved_news = [news_entity] # Notícia está na lista

    with patch.object(db.session, 'get') as mock_get, \
         patch.object(db.session, 'commit') as mock_commit:
        mock_get.side_effect = [user_entity, news_entity]
        user_repository.remove_favorite_news(user_id=1, news_id=10)

    assert news_entity not in user_entity.saved_news
    mock_commit.assert_called_once()

def test_remove_favorite_news_user_not_found(user_repository, db):

    with patch.object(db.session, 'get', return_value=None):
        with pytest.raises(UserNotFoundError):
            user_repository.remove_favorite_news(user_id=999, news_id=10)

def test_remove_favorite_news_not_favorited(user_repository, db):

    user_entity = UserEntity(id=1, full_name="Test", email="test@test.com", password_hash="hash")
    news_entity = NewsEntity(id=10, title="News", url="http://news.com")
    user_entity.saved_news = []

    with patch.object(db.session, 'get') as mock_get:
        mock_get.side_effect = [user_entity, news_entity]
        with pytest.raises(NewsNotFavoritedError):
            user_repository.remove_favorite_news(user_id=1, news_id=10)

def test_remove_favorite_news_sqlalchemy_error(user_repository, db):

    user_entity = UserEntity(id=1, full_name="Test", email="test@test.com", password_hash="hash")
    news_entity = NewsEntity(id=10, title="News", url="http://news.com")
    user_entity.saved_news = [news_entity]

    with patch.object(db.session, 'get') as mock_get:
        with patch.object(db.session, 'commit', side_effect=SQLAlchemyError("DB Error")) as mock_commit, \
             patch.object(db.session, 'rollback') as mock_rollback:
            mock_get.side_effect = [user_entity, news_entity]
            with pytest.raises(SQLAlchemyError):
                user_repository.remove_favorite_news(user_id=1, news_id=10)
            mock_rollback.assert_called_once()
