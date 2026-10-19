from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.core.exceptions.errors import (
    PedidoNaoEncontrado,
    PedidoNaoPodeSerEntregue,
    PedidoNaoPodeSerFinalizado,
)
from app.services import pedidos as modulo  # ajuste o caminho se for outro
from app.services.pedidos import PedidosService, StatusPedido

ABERTO = StatusPedido.ABERTO
PRONTO = StatusPedido.PRONTO
ENTREGUE = StatusPedido.ENTREGUE


# ---------- fixtures e helpers ----------

@pytest.fixture
def service():
    """Service com o repositório trocado por um mock (sem banco de dados)."""
    svc = PedidosService(session=MagicMock())
    svc.repo = MagicMock()
    return svc


def _pedido(status: str):
    pedido = MagicMock()
    pedido.status = status
    return pedido


# ---------- atualiza_status_pedido: pedido inexistente ----------

def test_pedido_nao_encontrado(service):
    service.repo.get_pedido.return_value = None

    with pytest.raises(PedidoNaoEncontrado):
        service.atualiza_status_pedido(1, 1, PRONTO)

    service.repo.update_status_pedido.assert_not_called()


# ---------- atualiza_status_pedido: transições permitidas ----------

@pytest.mark.parametrize(
    "atual, novo",
    [
        (ABERTO, PRONTO),
        (PRONTO, ENTREGUE),
        (ENTREGUE, ENTREGUE),  # idempotente
        (ABERTO, ABERTO),      # sem regra para ABERTO (comportamento atual)
        (PRONTO, ABERTO),      # sem regra para ABERTO (comportamento atual)
    ],
)
def test_transicoes_permitidas(service, atual, novo):
    pedido = _pedido(atual.value)
    service.repo.get_pedido.return_value = pedido

    service.atualiza_status_pedido(1, 1, novo)

    assert pedido.status == novo.value
    service.repo.update_status_pedido.assert_called_once_with(pedido)


# ---------- atualiza_status_pedido: transições bloqueadas ----------

@pytest.mark.parametrize(
    "atual, novo, erro",
    [
        (PRONTO, PRONTO, PedidoNaoPodeSerFinalizado),
        (ENTREGUE, PRONTO, PedidoNaoPodeSerFinalizado),
        (ABERTO, ENTREGUE, PedidoNaoPodeSerEntregue),
    ],
)
def test_transicoes_bloqueadas(service, atual, novo, erro):
    pedido = _pedido(atual.value)
    service.repo.get_pedido.return_value = pedido

    with pytest.raises(erro):
        service.atualiza_status_pedido(1, 1, novo)

    # status não pode ter sido alterado e nada pode ter sido salvo
    assert pedido.status == atual.value
    service.repo.update_status_pedido.assert_not_called()


def test_repositorio_recebe_ids_corretos(service):
    service.repo.get_pedido.return_value = _pedido("ABERTO")

    service.atualiza_status_pedido(pedido_id=10, empresa_id=20, status=PRONTO)

    service.repo.get_pedido.assert_called_once_with(10, 20)


# ---------- criar_pedido ----------

def test_criar_pedido_define_status_aberto_e_ids(service, monkeypatch):
    # Troca o Pedido (modelo do banco) por um objeto simples que guarda os argumentos
    class PedidoFalso:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    monkeypatch.setattr(modulo, "Pedido", PedidoFalso)

    cadastro = MagicMock()
    cadastro.model_dump.return_value = {"descricao": "2 cervejas"}

    service.criar_pedido(cadastro, usuario_id=5, empresa_id=9)

    pedido_criado = service.repo.create.call_args[0][0]
    assert pedido_criado.descricao == "2 cervejas"
    assert pedido_criado.usuario_id == 5
    assert pedido_criado.empresa_id == 9
    assert pedido_criado.status == "ABERTO"


# ---------- _intervalo_expediente ----------

@pytest.mark.parametrize(
    "agora, inicio_esperado, fim_esperado",
    [
        # durante o dia
        (datetime(2026, 10, 19, 10, 0), datetime(2026, 10, 19, 7, 0), datetime(2026, 10, 20, 6, 0)),
        # exatamente 07:00 -> começa expediente novo
        (datetime(2026, 10, 19, 7, 0), datetime(2026, 10, 19, 7, 0), datetime(2026, 10, 20, 6, 0)),
        # 23:59 -> ainda no expediente que começou hoje
        (datetime(2026, 10, 19, 23, 59), datetime(2026, 10, 19, 7, 0), datetime(2026, 10, 20, 6, 0)),
        # meia-noite -> expediente que começou ontem
        (datetime(2026, 10, 20, 0, 0), datetime(2026, 10, 19, 7, 0), datetime(2026, 10, 20, 6, 0)),
        # madrugada
        (datetime(2026, 10, 20, 2, 0), datetime(2026, 10, 19, 7, 0), datetime(2026, 10, 20, 6, 0)),
        # 06:59 -> antes das 07h ainda usa o expediente de ontem
        (datetime(2026, 10, 20, 6, 59), datetime(2026, 10, 19, 7, 0), datetime(2026, 10, 20, 6, 0)),
    ],
)
def test_intervalo_expediente(agora, inicio_esperado, fim_esperado):
    inicio, fim = PedidosService._intervalo_expediente(agora)

    assert inicio == inicio_esperado
    assert fim == fim_esperado


def test_intervalo_virada_de_mes():
    inicio, fim = PedidosService._intervalo_expediente(datetime(2026, 11, 1, 3, 0))

    assert inicio == datetime(2026, 10, 31, 7, 0)
    assert fim == datetime(2026, 11, 1, 6, 0)


# ---------- listagens ----------

def test_listar_ultimos_pedidos_usa_intervalo(service, monkeypatch):
    inicio = datetime(2026, 10, 19, 7, 0)
    fim = datetime(2026, 10, 20, 6, 0)
    monkeypatch.setattr(PedidosService, "_intervalo_expediente", staticmethod(lambda: (inicio, fim)))

    resultado = service.listar_ultimos_pedidos(empresa_id=3)

    service.repo.get_ultimos_pedidos.assert_called_once_with(3, inicio, fim)
    assert resultado == service.repo.get_ultimos_pedidos.return_value


def test_listar_pedidos_bartender_usa_intervalo(service, monkeypatch):
    inicio = datetime(2026, 10, 19, 7, 0)
    fim = datetime(2026, 10, 20, 6, 0)
    monkeypatch.setattr(PedidosService, "_intervalo_expediente", staticmethod(lambda: (inicio, fim)))

    resultado = service.listar_pedidos_bartender(usuario_id=7, empresa_id=3)

    service.repo.get_bartender_ultimos_pedidos.assert_called_once_with(7, 3, inicio, fim)
    assert resultado == service.repo.get_bartender_ultimos_pedidos.return_value
