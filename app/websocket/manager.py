from fastapi import WebSocket

from app.schemas.auth import Auth
from app.core.logger import logger

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, dict[int, WebSocket]] = {
            "expositor":{},
            "cozinha":{},
            "bartender":{}
        }

    async def connect(self, websocket: WebSocket, usuario: Auth):
        await websocket.accept()
        
        antiga = self.connections.get(usuario.role, {}).get(usuario.sub)
        if antiga and antiga is not websocket:
            await antiga.close(code=4000, reason="Nova conexão estabelecida")

        self.connections[usuario.role][usuario.sub] = websocket

        logger.info(f"Conexão criada. Usuário: {usuario.sub}, Conexões ativas: {sum(len(conexoes) for conexoes in self.connections.values())}")

    async def broadcast_role(self, role: str, mensagem: dict):
        conexoes = list(self.connections.get(role, {}).items())
        mortos = []

        for user_id, websocket in conexoes:
            try:
                await websocket.send_json(mensagem)
            except Exception as e:
                logger.warning(f"Falha ao enviar para usuário {user_id} ({role}): {e}")
                mortos.append(user_id)

        for user_id in mortos:
            self.connections[role].pop(user_id, None)

    async def send_user(self, user_id: int, mensagem: dict):
        for role, conexoes in self.connections.items():
            websocket = conexoes.get(user_id)
            if websocket:
                await websocket.send_json(mensagem)
                return
        logger.warning(f"Usuário {user_id} não conectado, mensagem não entregue: {mensagem.get('event')}")

    async def disconnect(self, websocket: WebSocket, user_id: int, role: str):
        conexao = self.connections.get(role, {}).get(user_id)

        if conexao is websocket:
            self.connections[role].pop(user_id, None)

            logger.info(
                f"Conexão finalizada. usuário: {user_id}"
            )

manager = ConnectionManager()