from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database.connection import get_db
from app.core.security.auth import create_token
from tests.conftest import session

# -----------------------------------------------------------------------------------------
#
# ### FAKE DATA ###
#
# ------------------------------------------------------------------------------------------


fake_client_data = {
    "pedido_valido": {"drink": "drink-teste", "cliente_nome": "cliente-teste",},
    "pedido_sem_token": {"drink": "drink-teste", "cliente_nome": "cliente-teste",}
}

fake_payload = {
    "bartender": {
        "sub": "1",
        "role": "bartender",
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=6),
    },
    "cozinha": {
        "sub": "2",
        "role": "cozinha",
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=6),
    }
}

# -----------------------------------------------------------------------------------------
#
# ### CONFIG ###
#
# -----------------------------------------------------------------------------------------


@pytest.fixture
def client(session):
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture
def token_bartender():
    return create_token(fake_payload["bartender"])

@pytest.fixture
def token_cozinha():
    return create_token(fake_payload["cozinha"])

def auth(token):
    return {"Authorization": f"Bearer {token}"}

# -----------------------------------------------------------------------------------------
#
# ### TESTS ###
#
# -----------------------------------------------------------------------------------------

def test_criar_pedido(client, token_bartender):
    response = client.post(
        "/pedidos/",
        json=fake_client_data["pedido_valido"],
        headers=auth(token_bartender),
    )

    assert response.status_code == 200

    dados = response.json()
    assert dados["drink"] == "drink-teste"
    assert dados["cliente_nome"] == "cliente-teste"
    assert dados["status"] == "ABERTO"

def test_criar_pedido_dados_invalidos(client, token_bartender):
    response = client.post(
        "/pedidos/",
        json={},
        headers=auth(token_bartender),
    )

    assert response.status_code == 422

def test_listar_pedidos_cozinha(client, token_cozinha):
    response = client.get(
        "/pedidos/",
        headers=auth(token_cozinha),
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_listar_pedidos_bartender(client, token_bartender):
    response = client.get(
        "/pedidos/bartender",
        headers=auth(token_bartender),
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)

# ACHO QUE ESSE NÃO PRECISA ESTAR AQUI
def test_listar_pedidos_sem_token(client):
    response = client.get("/pedidos/")    

    assert response.status_code == 401

def test_criar_pedido_sem_token(client):
    response = client.post(
        "/pedidos/",
        json=fake_client_data["pedido_sem_token"]
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}