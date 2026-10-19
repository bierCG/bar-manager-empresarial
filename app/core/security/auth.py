import datetime

import jwt
from fastapi import WebSocket, HTTPException, Depends,  WebSocketException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import Auth

from app.core.exceptions.errors import ErroOperacional

oauth_scheme = HTTPBearer()

from app.core.settings import settings

def requer_roles(*permitidas):
    def verificar(usuario: Auth = Depends(autenticar_usuario)):
        if usuario.role not in permitidas:
            raise HTTPException(status_code=403, detail="Acesso negado")
        return usuario
    return verificar

def create_token(payload: dict) -> str:
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

def validate_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado") from None
    
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Token inválido") from None

async def autenticar_ws(websocket: WebSocket) -> Auth:
    token = websocket.query_params.get("token")

    if not token:
        raise WebSocketException(code=1008, reason="Token não informado")

    payload = validate_token(token)

    return Auth.model_validate(payload)

def autenticar_usuario(
    credenciais: HTTPAuthorizationCredentials = Depends(oauth_scheme)
) -> Auth:
    token = credenciais.credentials

    if not token:
        raise ErroOperacional("Token não informado")

    payload = validate_token(token)

    return Auth.model_validate(payload)