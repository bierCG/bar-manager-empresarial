from app.websocket.manager import manager

async def notificar_pedido(evento: str, pedido, user_id: int):
    mensagem = {"event": evento, "payload": pedido}
    await manager.send_user(user_id, mensagem)
    await manager.broadcast_role("cozinha", mensagem)

async def notificar_cozinha(evento: str, pedido):
    mensagem = {"event": evento, "payload": pedido}
    await manager.broadcast_role("cozinha", mensagem)

async def notificar_expositor(evento: str, pedido):
    mensagem = {"event": evento, "payload": pedido}
    await manager.broadcast_role("pv", mensagem)