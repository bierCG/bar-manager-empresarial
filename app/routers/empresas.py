from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.empresa import (
    CreateRequestEmpresa,
    CreateResponseEmpresa,
    UpdateResponseEmpresa,
    UpdateRequestEmpresa,
    ReadResponseEmpresa
)

from app.services.empresas import EmpresaService
from app.core.security.auth import requer_roles
from app.core.database.connection import get_db

router = APIRouter(prefix="/empresas", tags=["Empresas"])

def get_service(session: Session = Depends(get_db)) -> EmpresaService:
    return EmpresaService(session)

# ------------------------------------------------------------------------------------------
#
# ### POST ###
#
# ------------------------------------------------------------------------------------------

@router.post(
    "/",
    dependencies=[Depends(requer_roles('admin'))],
    response_model=CreateResponseEmpresa
)
def cadastrar_empresa(
    cadastro: CreateRequestEmpresa,
    service: EmpresaService = Depends(get_service)
):
    return service.cadastrar(cadastro)

# ------------------------------------------------------------------------------------------
#
# ### PATCH ###
#
# ------------------------------------------------------------------------------------------

@router.patch(
    "/{empresa_id}",
    dependencies=[Depends(requer_roles('admin'))],
    response_model=UpdateResponseEmpresa
)
def atualizar_cadastro_empresa(
    empresa_id: int,
    dados: UpdateRequestEmpresa,
    service: EmpresaService = Depends(get_service)
):
    return service.atualizar_cadastro(dados, empresa_id)

# ------------------------------------------------------------------------------------------
#
# ### GET ###
#
# ------------------------------------------------------------------------------------------

@router.get(
    "/",
    dependencies=[Depends(requer_roles('admin'))],
    response_model=list[ReadResponseEmpresa]
)
def listar_empresas(service: EmpresaService = Depends(get_service)):
    return service.listar_empresas()