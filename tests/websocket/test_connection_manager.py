from unittest.mock import AsyncMock

import pytest

from app.websocket.manager import ConnectionManager
from app.schemas.auth import Auth


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def usuario():
    return Auth(sub="1", role="bartender")


@pytest.mark.asyncio
async def test_connect(manager, usuario):
    websocket = AsyncMock()

    await manager.connect(websocket, usuario)

    websocket.accept.assert_awaited_once()
    assert manager.connections["bartender"][1] is websocket


@pytest.mark.asyncio
async def test_connect_substitui_conexao_antiga(manager, usuario):
    antiga = AsyncMock()
    nova = AsyncMock()

    await manager.connect(antiga, usuario)
    await manager.connect(nova, usuario)

    antiga.close.assert_awaited_once_with(
        code=4000,
        reason="Nova conexão estabelecida"
    )

    assert manager.connections["bartender"][1] is nova


@pytest.mark.asyncio
async def test_broadcast_role(manager):
    ws1 = AsyncMock()
    ws2 = AsyncMock()

    manager.connections["bartender"][1] = ws1
    manager.connections["bartender"][2] = ws2

    mensagem = {
        "event": "pedido.created",
        "payload": {"id": 10}
    }

    await manager.broadcast_role("bartender", mensagem)

    ws1.send_json.assert_awaited_once_with(mensagem)
    ws2.send_json.assert_awaited_once_with(mensagem)


@pytest.mark.asyncio
async def test_send_user(manager):
    websocket = AsyncMock()
    manager.connections["bartender"][1] = websocket

    mensagem = {
        "event": "pedido.updated"
    }

    await manager.send_user(1, mensagem)

    websocket.send_json.assert_awaited_once_with(mensagem)


@pytest.mark.asyncio
async def test_send_user_nao_conectado(manager):
    await manager.send_user(99, {"event": "teste"})

    # Não deve lançar exceção


@pytest.mark.asyncio
async def test_disconnect(manager, usuario):
    websocket = AsyncMock()

    manager.connections["bartender"][1] = websocket

    await manager.disconnect(websocket, 1, "bartender")

    assert 1 not in manager.connections["bartender"]

@pytest.mark.asyncio
async def test_broadcast_remove_conexao_com_falha(manager):
    websocket = AsyncMock()
    websocket.send_json.side_effect = Exception("conexão perdida")

    manager.connections["bartender"][1] = websocket

    await manager.broadcast_role(
        "bartender",
        {"event": "teste"}
    )

    assert 1 not in manager.connections["bartender"]

@pytest.mark.asyncio
async def test_disconnect_nao_remove_nova_conexao(manager, usuario):
    antiga = AsyncMock()
    nova = AsyncMock()

    await manager.connect(antiga, usuario)
    await manager.connect(nova, usuario)

    await manager.disconnect(antiga, 1, "bartender")

    assert manager.connections["bartender"][1] is nova