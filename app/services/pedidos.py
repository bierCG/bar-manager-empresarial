from datetime import date, datetime, time, timedelta
from enum import Enum

from sqlalchemy.orm import Session

from app.core.database.models import Pedido
from app.core.exceptions.errors import (
    PedidoNaoEncontrado,
    PedidoNaoPodeSerEntregue,
    PedidoNaoPodeSerFinalizado,
)
from app.repositories.pedidos import PedidoRepository
from app.schemas.pedido import CreateRequest


class StatusPedido(str, Enum):
    ABERTO = "ABERTO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"

REGRAS_TRANSICAO = {
    StatusPedido.PRONTO: (
        {StatusPedido.ABERTO},
        PedidoNaoPodeSerFinalizado,
    ),
    StatusPedido.ENTREGUE: (
        {StatusPedido.PRONTO, StatusPedido.ENTREGUE},
        PedidoNaoPodeSerEntregue,
    ),
}

INICIO_EXPEDIENTE = time(7)
FIM_EXPEDIENTE = time(6)


class PedidosService:
    def __init__(self, session: Session):
        self.repo = PedidoRepository(session)

    @staticmethod
    def _intervalo_expediente(agora: datetime | None = None) -> tuple[datetime, datetime]:
        agora = agora or datetime.now()

        dia_base = agora.date() if agora.time() >= INICIO_EXPEDIENTE else agora.date() - timedelta(days=1)

        inicio = datetime.combine(dia_base, INICIO_EXPEDIENTE)
        fim = datetime.combine(dia_base + timedelta(days=1), FIM_EXPEDIENTE)
        return inicio, fim

    def _obter_pedido_ou_erro(self, pedido_id: int, empresa_id: int) -> Pedido:
        pedido = self.repo.get_pedido(pedido_id, empresa_id)
        if not pedido:
            raise PedidoNaoEncontrado
        return pedido

    @staticmethod
    def _validar_transicao(atual: StatusPedido, novo: StatusPedido) -> None:
        regra = REGRAS_TRANSICAO.get(novo)
        if regra is None:
            return
        origens_permitidas, erro = regra
        if atual not in origens_permitidas:
            raise erro

    def criar_pedido(self, cadastro: CreateRequest, usuario_id: int, empresa_id: int) -> Pedido:
        pedido = Pedido(
            **cadastro.model_dump(),
            usuario_id=usuario_id,
            empresa_id=empresa_id,
            status=StatusPedido.ABERTO.value,
        )
        return self.repo.create(pedido)

    def atualiza_status_pedido(self, pedido_id: int, empresa_id: int, status: StatusPedido) -> Pedido:
        pedido = self._obter_pedido_ou_erro(pedido_id, empresa_id)
        self._validar_transicao(StatusPedido(pedido.status), status)

        pedido.status = status.value
        return self.repo.update_status_pedido(pedido)

    def listar_ultimos_pedidos(self, empresa_id: int):
        inicio, fim = self._intervalo_expediente()
        return self.repo.get_ultimos_pedidos(empresa_id, inicio, fim)

    def listar_pedidos_bartender(self, usuario_id: int, empresa_id: int):
        inicio, fim = self._intervalo_expediente()
        return self.repo.get_bartender_ultimos_pedidos(usuario_id, empresa_id, inicio, fim)