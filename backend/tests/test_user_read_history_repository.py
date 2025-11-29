import pytest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime, timedelta

from app.repositories.user_read_history_repository import UserReadHistoryRepository
from app.entities.user_read_history_entity import UserReadHistoryEntity
from app.models.exceptions import UserNotFoundError, NewsNotFoundError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


@pytest.fixture
def mock_session():
    """Fixture para mockar a sessão do SQLAlchemy."""
    session = MagicMock()
    # Mock para a query de existência de usuário/notícia
    session.query.return_value.filter_by.return_value.exists.return_value = session.query.return_value
    return session


@pytest.fixture
def repository(mock_session):
    """Fixture que cria uma instância do repositório com a sessão mockada."""
    return UserReadHistoryRepository(session=mock_session)


@pytest.fixture
def mock_history_entity():
    """Fixture que cria uma entidade de histórico mockada."""
    mock_entity = MagicMock()
    mock_entity.id = 1
    mock_entity.user_id = 1
    mock_entity.news_id = 100
    mock_entity.read_at = datetime.now()
    return mock_entity


def test_create_new_history_record_success(repository, mock_session):
    """
    Testa a criação de um novo registro de histórico quando não há leitura no dia.
    """
    user_id, news_id = 1, 100

    with patch.object(repository, 'find_today_read', return_value=None):
        # Simula que usuário e notícia existem
        mock_session.query.return_value.scalar.side_effect = [True, True]

        entity, created = repository.create(user_id, news_id)

        assert created is True
        assert entity.user_id == user_id
        assert entity.news_id == news_id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(entity)


def test_create_updates_existing_record_today(repository, mock_session, mock_history_entity):
    """
    Testa a atualização de um registro de histórico se a notícia já foi lida no mesmo dia.
    """
    user_id, news_id = 1, 100
    updated_entity = MagicMock()

    with patch.object(repository, 'find_today_read', return_value=mock_history_entity), \
         patch.object(repository, 'update_read_at', return_value=updated_entity) as mock_update:

        entity, created = repository.create(user_id, news_id)

        assert created is False
        assert entity == updated_entity
        mock_update.assert_called_once_with(mock_history_entity)
        mock_session.add.assert_not_called() # Não deve adicionar um novo


def test_create_user_not_found(repository, mock_session):
    """
    Testa se UserNotFoundError é levantada quando o usuário não existe.
    """
    with patch.object(repository, 'find_today_read', return_value=None):
        # Simula que o usuário não existe
        mock_session.query.return_value.scalar.return_value = False

        with pytest.raises(UserNotFoundError, match="Usuário com ID 1 não encontrado."):
            repository.create(user_id=1, news_id=100)

        mock_session.rollback.assert_called_once()


def test_create_news_not_found(repository, mock_session):
    """
    Testa se NewsNotFoundError é levantada quando a notícia não existe.
    """
    with patch.object(repository, 'find_today_read', return_value=None):
        # Simula que o usuário existe, mas a notícia não
        mock_session.query.return_value.scalar.side_effect = [True, False]

        with pytest.raises(NewsNotFoundError, match="Notícia com ID 100 não encontrada."):
            repository.create(user_id=1, news_id=100)

        mock_session.rollback.assert_called_once()


def test_create_integrity_error(repository, mock_session):
    """
    Testa o tratamento de IntegrityError durante a criação.
    """
    mock_session.commit.side_effect = IntegrityError("mock", "mock", "mock")

    with patch.object(repository, 'find_today_read', return_value=None):
        mock_session.query.return_value.scalar.side_effect = [True, True]

        with pytest.raises(Exception, match="Erro de integridade ao salvar histórico de leitura."):
            repository.create(user_id=1, news_id=100)

        mock_session.rollback.assert_called_once()


def test_update_read_at_success(repository, mock_session, mock_history_entity):
    """
    Testa a atualização bem-sucedida do timestamp de leitura.
    """
    before_update = mock_history_entity.read_at
    
    updated_entity = repository.update_read_at(mock_history_entity)

    assert updated_entity.read_at > before_update
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(updated_entity)


def test_update_read_at_sqlalchemy_error(repository, mock_session, mock_history_entity):
    """
    Testa o tratamento de SQLAlchemyError durante a atualização.
    """
    mock_session.commit.side_effect = SQLAlchemyError("DB Error")

    with pytest.raises(Exception, match="Erro ao atualizar histórico de leitura."):
        repository.update_read_at(mock_history_entity)

    mock_session.rollback.assert_called_once()


@patch('app.repositories.user_read_history_repository.datetime')
def test_find_today_read_found(mock_dt, repository, mock_session, mock_history_entity):
    """
    Testa a busca por um registro de leitura no dia atual.
    """
    # Configura o mock de datetime para ter um valor fixo
    today = datetime(2024, 1, 1)
    mock_dt.today.return_value = today
    mock_dt.combine.side_effect = lambda d, t: datetime.combine(d, t)

    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_history_entity

    result = repository.find_today_read(user_id=1, news_id=100)

    assert result == mock_history_entity
    mock_session.execute.assert_called_once()


def test_find_today_read_not_found(repository, mock_session):
    """
    Testa o cenário onde nenhum registro é encontrado para o dia.
    """
    mock_session.execute.return_value.scalar_one_or_none.return_value = None

    result = repository.find_today_read(user_id=1, news_id=100)

    assert result is None


def test_find_today_read_sqlalchemy_error(repository, mock_session):
    """
    Testa o tratamento de erro na busca de leitura do dia.
    """
    mock_session.execute.side_effect = SQLAlchemyError("DB Error")

    with pytest.raises(Exception, match="Erro ao verificar histórico do dia."):
        repository.find_today_read(user_id=1, news_id=100)


def test_get_user_history_success(repository, mock_session, mock_history_entity):
    """
    Testa a busca paginada do histórico de um usuário.
    """
    mock_news_entity = MagicMock()
    mock_results = [(mock_history_entity, mock_news_entity)]
    total_count = 15

    # O primeiro execute é para o total, o segundo para os resultados paginados
    mock_session.execute.side_effect = [
        MagicMock(scalar=MagicMock(return_value=total_count)),
        MagicMock(all=MagicMock(return_value=mock_results))
    ]

    results, total = repository.get_user_history(user_id=1, page=2, per_page=5)

    assert total == total_count
    assert results == mock_results
    assert mock_session.execute.call_count == 2


def test_get_user_history_empty(repository, mock_session):
    """
    Testa a busca de histórico para um usuário sem registros.
    """
    mock_session.execute.side_effect = [
        MagicMock(scalar=MagicMock(return_value=0)),
        MagicMock(all=MagicMock(return_value=[]))
    ]

    results, total = repository.get_user_history(user_id=1)

    assert total == 0
    assert results == []


def test_get_user_history_sqlalchemy_error(repository, mock_session):
    """
    Testa o tratamento de erro na busca de histórico do usuário.
    """
    mock_session.execute.side_effect = SQLAlchemyError("DB Error")

    with pytest.raises(Exception, match="Erro ao buscar histórico de leitura."):
        repository.get_user_history(user_id=1)


def test_count_user_history_success(repository, mock_session):
    """
    Testa a contagem de registros de histórico de um usuário.
    """
    mock_session.execute.return_value.scalar.return_value = 25

    count = repository.count_user_history(user_id=1)

    assert count == 25
    mock_session.execute.assert_called_once()


def test_count_user_history_no_history(repository, mock_session):
    """
    Testa a contagem quando o usuário não tem histórico.
    """
    mock_session.execute.return_value.scalar.return_value = 0

    count = repository.count_user_history(user_id=1)

    assert count == 0