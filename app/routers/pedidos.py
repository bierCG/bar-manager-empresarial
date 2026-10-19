from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security.auth import requer_roles
from app.schemas.auth import Auth
from app.schemas.pedido import CreateRequest, CreateResponse
from app.services.pedidos import PedidosService
from app.core.database.connection import get_db

from app.websocket.notify import notificar_cozinha, notificar_pedido, notificar_expositor

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

def get_service(session: Session = Depends(get_db)) -> PedidosService:
    return PedidosService(session)

# ------------------------------------------------------------------------------------------
#
# ### POST ###
#
# ------------------------------------------------------------------------------------------

@router.post("/", response_model=CreateResponse)
async def criar_pedido(
    pedido: CreateRequest,
    userAuth: Auth = Depends(requer_roles('bartender')),
    service: PedidosService = Depends(get_service),
):
    pedido = service.criar_pedido(pedido, userAuth.sub, userAuth.empresa)

    response_ws = CreateResponse.model_validate(pedido).model_dump(mode="json")

    await notificar_cozinha("pedido.created", response_ws)
    await notificar_expositor("pedido.created", response_ws)

    return pedido

# ------------------------------------------------------------------------------------------
#
# ### PATCH ###
#
# ------------------------------------------------------------------------------------------

@router.patch(
    "/{pedido_id}/status/{status}",
    response_model=CreateResponse
)
async def atualizar_status_pedido(
    pedido_id: int,
    status: str,
    userAuth: Auth = Depends(requer_roles('cozinha')),
    service: PedidosService = Depends(get_service)
):
    pedido = service.atualiza_status_pedido(pedido_id, userAuth.empresa_id, status)
    
    response_ws = CreateResponse.model_validate(pedido).model_dump(mode="json")

    await notificar_pedido("pedido.updated", response_ws, pedido.vendedor_id)
    await notificar_cozinha("pedido.updated", response_ws)
    await notificar_expositor("pedido.updated", response_ws)

    return pedido