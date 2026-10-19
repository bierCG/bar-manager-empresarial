from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.auth import Auth
from app.schemas.usuario import (
    CreateRequest,
    CreateResponse,
    UpdateRequest,
    UpdateResponse,
    ReadResponse
)

from app.services.usuarios import UsuarioService
from app.core.security.auth import requer_roles
from app.core.database.connection import get_db

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

def get_service(session: Session = Depends(get_db)) -> UsuarioService:
    return UsuarioService(session)

# ------------------------------------------------------------------------------------------
#
# ### POST ###
#
# ------------------------------------------------------------------------------------------

@router.post("/", response_model=CreateResponse)
def cadastrar_usuario(
    cadastro: CreateRequest,
    auth: Auth = Depends(requer_roles('empresa')),
    service: UsuarioService = Depends(get_service)
):
    return service.cadastrar(cadastro, auth.sub)

# ------------------------------------------------------------------------------------------
#
# ### PATCH ###
#
# ------------------------------------------------------------------------------------------

@router.patch("/{usuario_id}", response_model=UpdateResponse)
def atualizar_cadastro(
    usuario_id: int,
    dados: UpdateRequest,
    auth: Auth = Depends(requer_roles('empresa')),
    service: UsuarioService = Depends(get_service)
):
    return service.atualizar_cadastro(dados, usuario_id, auth.sub)

# ------------------------------------------------------------------------------------------
#
# ### GET ###
#
# ------------------------------------------------------------------------------------------

@router.get(
    "/", 
    response_model=list[ReadResponse]
)
def listar_usuarios(
    auth: Auth = Depends(requer_roles('empresa')),
    service: UsuarioService = Depends(get_service)
):
    return service.listar_usuarios_empresa(auth.sub)