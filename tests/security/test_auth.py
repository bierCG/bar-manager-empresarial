import datetime
import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.core.security.auth import create_token, validate_token
from app.core.settings import settings

# OAuthPasswordBearer is not tested here because it is part of FastAPI's security utilities and not custom logic.
# OAithPasswordBearer is a dependency that FastAPI provides to handle OAuth2 password flow, and its functionality is assumed to be correct as it is part of the FastAPI framework.
# >>>>>

client = TestClient(app)
 
fake_payloads = {
    "valid": {
        "sub": "1",
        "role": "bartender",
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=6),
    },
    "expired": {
        "sub": "1",
        "role": "bartender",
        "exp": datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(hours=1),
    },
}

# ------------------------------------------------------------------------------------------
#
# ### HTTP ###
#
# ------------------------------------------------------------------------------------------


def test_create_and_validate_token():
    token = create_token(fake_payloads["valid"])

    payload = validate_token(token)

    assert payload["sub"] == "1"
    assert payload["role"] == "bartender"
    assert "exp" in payload


def test_token_invalido():
    with pytest.raises(HTTPException) as exc:
        validate_token("token-invalido")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Token inválido"


def test_token_expirado():
    payload = fake_payloads["expired"]

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    with pytest.raises(HTTPException) as exc:
        validate_token(token)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Token expirado"


# ------------------------------------------------------------------------------------------
#
# ### WEBSOCKET ###
#
# ------------------------------------------------------------------------------------------


def test_websocket_sem_token():
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/bar"):
            pass

    assert exc.value.code == 1008


def test_websocket_token_invalido():
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/bar?token=token-invalido"):
            pass