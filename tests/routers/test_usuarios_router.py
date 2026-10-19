from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.core.database.connection import get_db
from app.core.security.auth import create_token

fake_payload = {
    "bartender": {
        "sub": "1",
        "role": "bartender",
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=6),
    },
    "admin": {
        "sub": "1",
        "role": "admin",
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=6),
    }
}

fake_data = {
    "usuario_valido": {
        "nome": "Novo Usuario",
        "email": "novo@teste.com",
        "role": "bartender",
        "senha": "123456"
    },
    "email_duplicado": {
        "nome": "Email duplicado",
        "email": "teste@email.com",
        "role": "bartender",
        "senha": "123456"
    }
}


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_listar_usuarios(client):
    token = create_token(fake_payload["admin"])

    response = client.get(
        "/usuarios/",
        headers=auth(token)
    )

    assert response.status_code == 200

    dados = response.json()

    assert isinstance(dados, list)
    assert len(dados) > 0
    assert all("id" in usuario for usuario in dados)


def test_criar_usuario(client):
    token = create_token(fake_payload["admin"])

    response = client.post(
        "/usuarios/",
        json=fake_data["usuario_valido"],
        headers=auth(token)
    ) 

    assert response.status_code == 200

    dados = response.json()

    assert dados["nome"] == "Novo Usuario"
    assert dados["email"] == "novo@teste.com"
    assert "senha" not in dados
    

'''
def test_criar_usuario_email_duplicado(client):
    token = create_token(fake_payload["admin"])

    response = client.post(
        "/usuarios/",
        json={fake_data["email_duplicado"]},
        headers=auth(token)
    )

    assert response.status_code == 422
'''
    

'''
def test_criar_usuario_sem_permissao(client):
    token = create_token(fake_payload["bartender"])

    response = client.post(
        "/usuarios/",
        json={
            "nome": "Novo Usuario",
            "email": "novo@teste.com",
            "role": "bartender",
            "senha": "123456"
        },
        headers=auth(token)
    )

    assert response.status_code == 403
'''