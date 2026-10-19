from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import DataError, IntegrityError

from app.core.database.models import Pedido, Produto, Usuario
from app.repositories.pedidos import PedidoRepository

# SEEDS: produto 1 e usuarios 1..3 pertencem a empresa 1; empresa 2 existe vazia
EMPRESA = 1
OUTRA_EMPRESA = 2

pedido_request = {
    "produto": 1,
    "usuario_id": 1,
    "empresa_id": EMPRESA,
    "status": "ABERTO",
}


def dt(dia):
    return datetime(2020, 1, dia, 12, 0, tzinfo=timezone.utc)


INICIO = datetime(2020, 1, 10, 0, 0, tzinfo=timezone.utc)
FIM = datetime(2020, 1, 20, 0, 0, tzinfo=timezone.utc)


def criar(session, **sobrescrever):
    dados = {**pedido_request, **sobrescrever}
    return PedidoRepository(session).create(Pedido(**dados))


def ids(pedidos):
    return {p.id for p in pedidos}


def aplicar(repo, pedido, dados):
    for campo, valor in dados.items():
        setattr(pedido, campo, valor)
    return repo.update_status_pedido(pedido)


def montar_empresa_2(session):
    """Cria produto e usuario na empresa 2 e devolve seus ids."""
    produto = Produto(nome="Produto Emp2", valor=10.0, empresa_id=OUTRA_EMPRESA)
    usuario = Usuario(
        nome="Usuario Emp2",
        usuario="usuario_emp2",
        role="barman",
        senha_hash="x",
        empresa_id=OUTRA_EMPRESA,
    )
    session.add_all([produto, usuario])
    session.flush()
    return produto.id, usuario.id


# ----------------------------------------------------------------------
# CREATE
# ----------------------------------------------------------------------

def test_create(session):
    resultado = criar(session)

    assert resultado.id is not None
    assert resultado.criado_em is not None  # server_default preenchido
    assert {k: getattr(resultado, k) for k in pedido_request} == pedido_request


def test_create_persiste_no_banco(session):
    criado = criar(session)

    session.expire_all()

    buscado = PedidoRepository(session).get_pedido(criado.id, EMPRESA)
    assert buscado is not None
    assert buscado.status == "ABERTO"


def test_create_status_livre_aceito(session):
    # nao ha enum nem CHECK: documenta a lacuna (validar no schema/service)
    assert criar(session, status="QUALQUER").status == "QUALQUER"


def test_create_status_no_limite(session):
    assert len(criar(session, status="X" * 20).status) == 20


def test_create_status_acima_do_limite(session):
    with pytest.raises(DataError):
        criar(session, status="X" * 21)


@pytest.mark.parametrize("campo", ["produto", "usuario_id", "empresa_id", "status"])
def test_create_campo_obrigatorio_nulo(session, campo):
    with pytest.raises(IntegrityError):
        criar(session, **{campo: None})


@pytest.mark.parametrize(
    "campo", ["produto", "usuario_id", "empresa_id"]
)
def test_create_fk_inexistente(session, campo):
    with pytest.raises(IntegrityError):
        criar(session, **{campo: 99999})


def test_create_referencias_de_outra_empresa_aceitas(session):
    # nao ha FK composta (id, empresa_id): o banco aceita pedido da empresa 2
    # apontando para produto e usuario da empresa 1. Documenta a lacuna.
    resultado = criar(session, empresa_id=OUTRA_EMPRESA)

    assert resultado.empresa_id == OUTRA_EMPRESA
    assert resultado.produto == 1


# ----------------------------------------------------------------------
# GET_PEDIDO
# ----------------------------------------------------------------------

def test_get_pedido(session):
    criado = criar(session)

    pedido = PedidoRepository(session).get_pedido(criado.id, EMPRESA)

    assert pedido is not None
    assert pedido.id == criado.id
    assert pedido.empresa_id == EMPRESA


def test_get_pedido_inexistente(session):
    assert PedidoRepository(session).get_pedido(999999, EMPRESA) is None


def test_get_pedido_outra_empresa(session):
    # multi-tenant: pedido da empresa 1 nao pode ser lido pela empresa 2
    criado = criar(session, empresa_id=EMPRESA)

    assert PedidoRepository(session).get_pedido(criado.id, OUTRA_EMPRESA) is None


# ----------------------------------------------------------------------
# GET_ULTIMOS_PEDIDOS
# ----------------------------------------------------------------------

def test_get_ultimos_pedidos_filtra_por_periodo(session):
    dentro = criar(session, criado_em=dt(15))
    antes = criar(session, criado_em=dt(5))
    depois = criar(session, criado_em=dt(25))

    resultado = ids(PedidoRepository(session).get_ultimos_pedidos(EMPRESA, INICIO, FIM))

    assert resultado == {dentro.id}
    assert antes.id not in resultado and depois.id not in resultado


def test_get_ultimos_pedidos_limites_inclusivos(session):
    no_inicio = criar(session, criado_em=INICIO)
    no_fim = criar(session, criado_em=FIM)

    resultado = ids(PedidoRepository(session).get_ultimos_pedidos(EMPRESA, INICIO, FIM))

    assert resultado == {no_inicio.id, no_fim.id}


def test_get_ultimos_pedidos_filtra_por_empresa(session):
    da_1 = criar(session, criado_em=dt(15), empresa_id=EMPRESA)
    da_2 = criar(session, criado_em=dt(15), empresa_id=OUTRA_EMPRESA)

    resultado = ids(PedidoRepository(session).get_ultimos_pedidos(EMPRESA, INICIO, FIM))

    assert resultado == {da_1.id}
    assert da_2.id not in resultado


def test_get_ultimos_pedidos_periodo_sem_pedidos(session):
    criar(session, criado_em=dt(15))

    vazio = PedidoRepository(session).get_ultimos_pedidos(
        EMPRESA,
        datetime(2000, 1, 1, tzinfo=timezone.utc),
        datetime(2000, 1, 2, tzinfo=timezone.utc),
    )

    assert vazio == []


def test_get_ultimos_pedidos_inicio_maior_que_fim(session):
    criar(session, criado_em=dt(15))

    assert PedidoRepository(session).get_ultimos_pedidos(EMPRESA, FIM, INICIO) == []


def test_get_ultimos_pedidos_empresa_sem_pedidos(session):
    assert PedidoRepository(session).get_ultimos_pedidos(9999, INICIO, FIM) == []


# ----------------------------------------------------------------------
# GET_BARTENDER_ULTIMOS_PEDIDOS
# ----------------------------------------------------------------------

def test_get_bartender_ultimos_pedidos_so_do_usuario(session):
    do_1 = criar(session, usuario_id=1, criado_em=dt(15))
    do_2 = criar(session, usuario_id=2, criado_em=dt(15))

    resultado = ids(
        PedidoRepository(session).get_bartender_ultimos_pedidos(1, EMPRESA, INICIO, FIM)
    )

    assert resultado == {do_1.id}
    assert do_2.id not in resultado


def test_get_bartender_ultimos_pedidos_filtra_por_periodo(session):
    dentro = criar(session, usuario_id=1, criado_em=dt(15))
    criar(session, usuario_id=1, criado_em=dt(5))
    criar(session, usuario_id=1, criado_em=dt(25))

    resultado = ids(
        PedidoRepository(session).get_bartender_ultimos_pedidos(1, EMPRESA, INICIO, FIM)
    )

    assert resultado == {dentro.id}


def test_get_bartender_ultimos_pedidos_outra_empresa(session):
    # o usuario 1 e da empresa 1, mas o pedido foi gravado na empresa 2
    criar(session, usuario_id=1, empresa_id=OUTRA_EMPRESA, criado_em=dt(15))

    resultado = PedidoRepository(session).get_bartender_ultimos_pedidos(
        1, EMPRESA, INICIO, FIM
    )

    assert resultado == []


def test_get_bartender_ultimos_pedidos_usuario_sem_pedidos(session):
    criar(session, usuario_id=1, criado_em=dt(15))

    resultado = PedidoRepository(session).get_bartender_ultimos_pedidos(
        3, EMPRESA, INICIO, FIM
    )

    assert resultado == []


def test_get_bartender_ultimos_pedidos_limites_inclusivos(session):
    no_inicio = criar(session, usuario_id=1, criado_em=INICIO)
    no_fim = criar(session, usuario_id=1, criado_em=FIM)

    resultado = ids(
        PedidoRepository(session).get_bartender_ultimos_pedidos(1, EMPRESA, INICIO, FIM)
    )

    assert resultado == {no_inicio.id, no_fim.id}


def test_get_ultimos_pedidos_empresa_2_com_dados_proprios(session):
    produto_id, usuario_id = montar_empresa_2(session)
    pedido = criar(
        session,
        produto=produto_id,
        usuario_id=usuario_id,
        empresa_id=OUTRA_EMPRESA,
        criado_em=dt(15),
    )

    resultado = ids(
        PedidoRepository(session).get_ultimos_pedidos(OUTRA_EMPRESA, INICIO, FIM)
    )

    assert resultado == {pedido.id}


# ----------------------------------------------------------------------
# UPDATE_STATUS_PEDIDO
# ----------------------------------------------------------------------

def test_update_status(session):
    repo = PedidoRepository(session)

    resultado = aplicar(repo, criar(session), {"status": "ENTREGUE"})

    assert resultado.status == "ENTREGUE"
    assert resultado.usuario_id == 1  # nao mexeu


def test_update_status_persiste_no_banco(session):
    repo = PedidoRepository(session)
    pedido = criar(session)
    aplicar(repo, pedido, {"status": "CANCELADO"})

    session.expire_all()

    assert repo.get_pedido(pedido.id, EMPRESA).status == "CANCELADO"


def test_update_status_para_o_mesmo_valor(session):
    repo = PedidoRepository(session)

    resultado = aplicar(repo, criar(session), {"status": "ABERTO"})

    assert resultado.status == "ABERTO"


def test_update_status_nulo(session):
    repo = PedidoRepository(session)

    with pytest.raises(IntegrityError):
        aplicar(repo, criar(session), {"status": None})


def test_update_status_acima_do_limite(session):
    repo = PedidoRepository(session)

    with pytest.raises(DataError):
        aplicar(repo, criar(session), {"status": "X" * 21})


@pytest.mark.parametrize("campo", ["produto", "usuario_id", "empresa_id"])
def test_update_fk_inexistente(session, campo):
    repo = PedidoRepository(session)

    with pytest.raises(IntegrityError):
        aplicar(repo, criar(session), {campo: 99999})
