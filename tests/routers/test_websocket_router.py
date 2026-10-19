from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.core.security.auth import create_token


client = TestClient(app)


fake_payload = {
    "bartender": {
        "sub": "1",
        "role": "bartender",
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=6),
    }
}


token = create_token(fake_payload["bartender"])


def test_websocket_conecta():
    with client.websocket_connect(f"/ws/bar?token={token}") as websocket:
        websocket.send_json({"event": "PING"})


def test_websocket_ping_pong():
    with client.websocket_connect(f"/ws/bar?token={token}") as websocket:
        websocket.send_json({"event": "PING"})
        resposta = websocket.receive_json()

        assert resposta == {"event": "PONG"}


def test_websocket_disconnect():
    with patch(
        "app.routers.websocket.manager.disconnect",
        new_callable=AsyncMock
    ) as disconnect:

        with client.websocket_connect(f"/ws/bar?token={token}"):
            pass

        disconnect.assert_awaited_once()