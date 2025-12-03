import pytest
from flask.testing import FlaskClient
from app.models.user import User
from app.models.news_source import NewsSource
from app.repositories.user_repository import UserRepository
from app.repositories.news_source_repository import NewsSourceRepository
from app.repositories.user_news_source_repository import UserNewsSourceRepository

def test_add_source_to_user_success(client: FlaskClient, db):
    user_model = User(full_name="Test User", email="sourceuser@example.com", password="Password123")
    source_model = NewsSource(name="New Source", url="http://newsource.com")
    
    user_repo = UserRepository(db.session)
    source_repo = NewsSourceRepository(db.session)
    user = user_repo.create(user_model)
    source = source_repo.create(source_model)

    auth_client, headers = get_auth_client(client, {"email": "sourceuser@example.com", "password": "Password123"})

    add_source_res = auth_client.post(
        "/news_sources/attach", 
        json={"source_id": source.id},
        headers=headers
    )
    assert add_source_res.status_code == 200
    assert add_source_res.json["success"] is True
    assert "Fonte associada com sucesso." in add_source_res.json["message"]

    user_source_repo = UserNewsSourceRepository(db.session)
    attached_ids = user_source_repo.get_user_preferred_source_ids(user.id)
    assert source.id in attached_ids

def test_add_existing_source_to_user(client: FlaskClient, db):
    user_model = User(full_name="Another User", email="anotheruser@example.com", password="Password123")
    source_model = NewsSource(name="Existing Source", url="http://existingsource.com")

    user_repo = UserRepository(db.session)
    source_repo = NewsSourceRepository(db.session)
    user = user_repo.create(user_model)
    source = source_repo.create(source_model)

    auth_client, headers = get_auth_client(client, {"email": "anotheruser@example.com", "password": "Password123"})

    # Adiciona a fonte uma vez (deve funcionar)
    add_source_res_1 = auth_client.post(
        "/news_sources/attach", 
        json={"source_id": source.id},
        headers=headers
    )
    assert add_source_res_1.status_code == 200
    assert add_source_res_1.json["success"] is True

    # Tenta adicionar a mesma fonte novamente (deve falhar)
    add_source_res_2 = auth_client.post(
        "/news_sources/attach", 
        json={"source_id": source.id},
        headers=headers
    )
    assert add_source_res_2.status_code == 409
    assert "A fonte de notícia já está associada a este usuário." in add_source_res_2.json["error"]

def test_add_source_missing_fields(client: FlaskClient, db):
    user_model = User(full_name="Test User 3", email="user3@example.com", password="Password123")
    user_repo = UserRepository(db.session)
    user_repo.create(user_model)
    
    auth_client, headers = get_auth_client(client, {"email": "user3@example.com", "password": "Password123"})

    add_source_res = auth_client.post(
        "/news_sources/attach", 
        json={},
        headers=headers
    )
    assert add_source_res.status_code == 400
    assert "source_id é obrigatório." in add_source_res.json["error"]

def test_list_user_sources(client: FlaskClient, db):
    user_model = User(full_name="List User", email="listuser@example.com", password="Password123")
    source1_model = NewsSource(name="Source One", url="http://sourceone.com")
    source2_model = NewsSource(name="Source Two", url="http://sourcetwo.com")

    user_repo = UserRepository(db.session)
    source_repo = NewsSourceRepository(db.session)
    user_source_repo = UserNewsSourceRepository(db.session)

    user = user_repo.create(user_model)
    source1 = source_repo.create(source1_model)
    source2 = source_repo.create(source2_model)

    user_source_repo.attach(user.id, source1.id)
    user_source_repo.attach(user.id, source2.id)

    auth_client, headers = get_auth_client(client, {"email": "listuser@example.com", "password": "Password123"})

    list_res = auth_client.get("/news_sources/list_all_attached_sources", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json["data"]
    assert len(data) == 2
    assert {item['name'] for item in data} == {"Source One", "Source Two"}

def test_remove_source_from_user(client: FlaskClient, db):
    user_model = User(full_name="Remove User", email="removeuser@example.com", password="Password123")
    source_model = NewsSource(name="Removable Source", url="http://removable.com")
    
    user_repo = UserRepository(db.session)
    source_repo = NewsSourceRepository(db.session)
    user_source_repo = UserNewsSourceRepository(db.session)

    user = user_repo.create(user_model)
    source = source_repo.create(source_model)
    user_source_repo.attach(user.id, source.id)

    auth_client, headers = get_auth_client(client, {"email": "removeuser@example.com", "password": "Password123"})

    remove_res = auth_client.delete(f"/news_sources/detach/{source.id}", headers=headers)
    assert remove_res.status_code == 200
    assert "Fonte desassociada com sucesso." in remove_res.json["message"]

    # Verifica se a associação foi realmente removida
    attached_ids = user_source_repo.get_user_preferred_source_ids(user.id)
    assert source.id not in attached_ids

def test_remove_non_existent_source(client: FlaskClient, db):
    user_model = User(full_name="Remove User 2", email="removeuser2@example.com", password="Password123")
    user_repo = UserRepository(db.session)
    user_repo.create(user_model)
    
    auth_client, headers = get_auth_client(client, {"email": "removeuser2@example.com", "password": "Password123"})

    remove_res = auth_client.delete("/news_sources/detach/999", headers=headers)
    assert remove_res.status_code == 404
    assert "Associação não encontrada para ser removida." in remove_res.json["error"]

def get_auth_client(client, user_data):
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }

    client.post(
        '/users/login',
        json=login_data,
    )
 
    csrf_cookie = client.get_cookie('csrf_access_token')
    csrf_token = ""
    if csrf_cookie:
        csrf_token = csrf_cookie.value
 
    headers = {'X-CSRF-TOKEN': csrf_token}
    return client, headers