from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.auth import Auth
from app.schemas.produto import (
    CreateRequest,
    CreateResponse,
    UpdateRequest,
    UpdateResponse
)

from app.services.produtos import ProdutoService
from app.core.security.auth import requer_roles
from app.core.database.connection import get_db

router = APIRouter(prefix="/produtos", tags=["Produtos"])

def get_service(session: Session = Depends(get_db)) -> ProdutoService:
    return ProdutoService(session)

# ------------------------------------------------------------------------------------------
#
# ### POST ###
#
# ------------------------------------------------------------------------------------------

@router.post("/", response_model=CreateResponse)
def cadastrar_produto(
    cadastro: CreateRequest,
    auth: Auth = Depends(requer_roles('empresa')),
    service: ProdutoService = Depends(get_service)
):
    return service.cadastrar_produto(cadastro, auth.sub)

@router.patch(
    "/{produto_id}",
    response_model=UpdateResponse
)
def atualizar_cadastro(
    dados: UpdateRequest,
    auth: Auth = Depends(requer_roles('empresa')),
    service: ProdutoService = Depends(get_service)
):
    return service.atualizar_cadastro(dados, auth.sub)