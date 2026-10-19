import pytest
from sqlalchemy.exc import DataError, IntegrityError

from app.core.database.models import Produto
from app.repositories.produtos import ProdutoRepository

EMPRESA = 1
OUTRA_EMPRESA = 2  # precisa existir nos seeds

produto_request = {"nome": "Caipirinha", "valor": 18.5}


def campos(obj, esperado):
    """Extrai de obj apenas as chaves de `esperado`, para comparar dicts."""
    return {k: getattr(obj, k) for k in esperado}


def criar(session, empresa_id=EMPRESA, **sobrescrever):
    dados = {**produto_request, **sobrescrever}
    return ProdutoRepository(session).create(Produto(**dados, empresa_id=empresa_id))


def aplicar(repo, produto, dados):
    for campo, valor in dados.items():
        setattr(produto, campo, valor)
    return repo.update(produto)


# ----------------------------------------------------------------------
# CREATE
# ----------------------------------------------------------------------

def test_create(session):
    resultado = criar(session)

    assert resultado.id is not None
    assert resultado.nome == produto_request["nome"]
    assert resultado.valor == pytest.approx(produto_request["valor"])
    assert resultado.empresa_id == EMPRESA


def test_create_persiste_no_banco(session):
    criado = criar(session)

    session.expire_all()

    buscado = ProdutoRepository(session).get_produto(criado.id, EMPRESA)
    assert buscado is not None
    assert buscado.nome == produto_request["nome"]


def test_create_nome_repetido_permitido(session):
    # nao ha unique em nome: documenta o comportamento atual
    primeiro = criar(session)
    segundo = criar(session)

    assert primeiro.id != segundo.id


def test_create_valor_negativo_aceito(session):
    # nao ha CHECK no banco: documenta a lacuna (validar no schema/service)
    assert criar(session, valor=-1.0).valor == pytest.approx(-1.0)


@pytest.mark.parametrize("campo", ["nome", "valor", "empresa_id"])
def test_create_campo_obrigatorio_nulo(session, campo):
    dados = {**produto_request, "empresa_id": EMPRESA, campo: None}

    with pytest.raises(IntegrityError):
        ProdutoRepository(session).create(Produto(**dados))


def test_create_empresa_inexistente(session):
    with pytest.raises(IntegrityError):
        criar(session, empresa_id=1000)


def test_create_nome_acima_do_limite(session):
    with pytest.raises(DataError):
        criar(session, nome="x" * 101)


def test_create_nome_no_limite(session):
    assert len(criar(session, nome="x" * 100).nome) == 100


# ----------------------------------------------------------------------
# GET_PRODUTO
# ----------------------------------------------------------------------

def test_get_produto(session):
    criado = criar(session)

    produto = ProdutoRepository(session).get_produto(criado.id, EMPRESA)

    assert produto is not None
    assert produto.id == criado.id
    assert produto.empresa_id == EMPRESA


def test_get_produto_inexistente(session):
    assert ProdutoRepository(session).get_produto(999999, EMPRESA) is None


def test_get_produto_outra_empresa(session):
    # multi-tenant: produto da empresa 1 nao pode ser lido pela empresa 2
    criado = criar(session, empresa_id=EMPRESA)

    assert ProdutoRepository(session).get_produto(criado.id, OUTRA_EMPRESA) is None


# ----------------------------------------------------------------------
# GET_ALL
# ----------------------------------------------------------------------

def test_get_all_inclui_recem_criado(session):
    criado = criar(session)

    produtos = ProdutoRepository(session).get_all(EMPRESA)

    assert criado.id in {p.id for p in produtos}


def test_get_all_filtra_por_empresa(session):
    da_1 = criar(session, empresa_id=EMPRESA)
    da_2 = criar(session, empresa_id=OUTRA_EMPRESA)

    produtos = ProdutoRepository(session).get_all(EMPRESA)
    ids = {p.id for p in produtos}

    assert da_1.id in ids
    assert da_2.id not in ids
    assert all(p.empresa_id == EMPRESA for p in produtos)


def test_get_all_empresa_sem_produtos(session):
    assert ProdutoRepository(session).get_all(9999) == []


# ----------------------------------------------------------------------
# UPDATE
# ----------------------------------------------------------------------

def test_update(session):
    repo = ProdutoRepository(session)
    dados = {"nome": "Nome Update", "valor": 25.0}

    resultado = aplicar(repo, criar(session), dados)

    assert resultado.nome == "Nome Update"
    assert resultado.valor == pytest.approx(25.0)


def test_update_apenas_nome(session):
    repo = ProdutoRepository(session)

    resultado = aplicar(repo, criar(session), {"nome": "So Nome"})

    assert resultado.nome == "So Nome"
    assert resultado.valor == pytest.approx(produto_request["valor"])


def test_update_apenas_valor(session):
    repo = ProdutoRepository(session)

    resultado = aplicar(repo, criar(session), {"valor": 99.9})

    assert resultado.valor == pytest.approx(99.9)
    assert resultado.nome == produto_request["nome"]


def test_update_persiste_no_banco(session):
    repo = ProdutoRepository(session)
    produto = criar(session)
    aplicar(repo, produto, {"nome": "Persistido"})

    session.expire_all()

    assert repo.get_produto(produto.id, EMPRESA).nome == "Persistido"


def test_update_empresa_inexistente(session):
    with pytest.raises(IntegrityError):
        aplicar(ProdutoRepository(session), criar(session), {"empresa_id": 1000})


@pytest.mark.parametrize("campo", ["nome", "valor"])
def test_update_campo_obrigatorio_nulo(session, campo):
    with pytest.raises(IntegrityError):
        aplicar(ProdutoRepository(session), criar(session), {campo: None})


def test_update_nome_acima_do_limite(session):
    with pytest.raises(DataError):
        aplicar(ProdutoRepository(session), criar(session), {"nome": "x" * 101})