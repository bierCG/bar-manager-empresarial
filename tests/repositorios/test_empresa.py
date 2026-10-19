import pytest
from sqlalchemy.exc import DataError, IntegrityError

from app.core.database.models import Empresa
from app.repositories.empresas import EmpresaRepository

# SEEDS
CNPJ_SEED_1 = "12345678901234"
USUARIO_SEED_1 = "empresa_teste"
CNPJ_SEED_2 = "12345678901230"
USUARIO_SEED_2 = "empresa_teste1"

empresa_request = {
    "nome": "Empresa Nova",
    "cnpj": "99999999999999",
    "usuario": "empresa_nova",
    "senha": "hash_qualquer",
}

CAMPOS = list(empresa_request)


def campos(obj, esperado):
    """Extrai de obj apenas as chaves de `esperado`, para comparar dicts."""
    return {k: getattr(obj, k) for k in esperado}


def aplicar(repo, empresa, dados):
    for campo, valor in dados.items():
        setattr(empresa, campo, valor)
    return repo.update(empresa)


# ----------------------------------------------------------------------
# CREATE
# ----------------------------------------------------------------------

def test_create(session):
    resultado = EmpresaRepository(session).create(Empresa(**empresa_request))

    assert resultado.id is not None
    assert campos(resultado, empresa_request) == empresa_request


def test_create_persiste_no_banco(session):
    repo = EmpresaRepository(session)
    repo.create(Empresa(**empresa_request))

    session.expire_all()

    buscada = repo.get_by_cnpj(empresa_request["cnpj"])
    assert buscada is not None
    assert buscada.nome == empresa_request["nome"]


def test_create_cnpj_duplicado(session):
    dados = {**empresa_request, "cnpj": CNPJ_SEED_1}

    with pytest.raises(IntegrityError):
        EmpresaRepository(session).create(Empresa(**dados))


def test_create_usuario_duplicado(session):
    dados = {**empresa_request, "usuario": USUARIO_SEED_1}

    with pytest.raises(IntegrityError):
        EmpresaRepository(session).create(Empresa(**dados))


@pytest.mark.parametrize("campo", CAMPOS)
def test_create_campo_obrigatorio_nulo(session, campo):
    dados = {**empresa_request, campo: None}

    with pytest.raises(IntegrityError):
        EmpresaRepository(session).create(Empresa(**dados))


@pytest.mark.parametrize("campo", CAMPOS)
def test_create_campo_ausente(session, campo):
    dados = {k: v for k, v in empresa_request.items() if k != campo}

    with pytest.raises(IntegrityError):
        EmpresaRepository(session).create(Empresa(**dados))


@pytest.mark.parametrize(
    "campo, tamanho",
    [("nome", 101), ("cnpj", 15), ("usuario", 101), ("senha", 256)],
)
def test_create_acima_do_limite(session, campo, tamanho):
    dados = {**empresa_request, campo: "9" * tamanho}

    with pytest.raises(DataError):
        EmpresaRepository(session).create(Empresa(**dados))


def test_create_cnpj_curto_aceito(session):
    # nao ha CHECK de tamanho minimo: documenta a lacuna (validar no schema)
    resultado = EmpresaRepository(session).create(Empresa(**{**empresa_request, "cnpj": "123"}))

    assert resultado.cnpj == "123"


# ----------------------------------------------------------------------
# GET_BY_USERNAME
# ----------------------------------------------------------------------

def test_get_by_username(session):
    empresa = EmpresaRepository(session).get_by_username(USUARIO_SEED_1)

    assert empresa is not None
    assert empresa.usuario == USUARIO_SEED_1
    assert empresa.cnpj == CNPJ_SEED_1


def test_get_by_username_inexistente(session):
    assert EmpresaRepository(session).get_by_username("nao_existe") is None


def test_get_by_username_diferencia_maiusculas(session):
    assert EmpresaRepository(session).get_by_username(USUARIO_SEED_1.upper()) is None


# ----------------------------------------------------------------------
# GET_BY_CNPJ
# ----------------------------------------------------------------------

def test_get_by_cnpj(session):
    empresa = EmpresaRepository(session).get_by_cnpj(CNPJ_SEED_2)

    assert empresa is not None
    assert empresa.cnpj == CNPJ_SEED_2
    assert empresa.usuario == USUARIO_SEED_2


def test_get_by_cnpj_inexistente(session):
    assert EmpresaRepository(session).get_by_cnpj("00000000000000") is None


def test_get_by_cnpj_formatado_nao_encontra(session):
    # a busca e por igualdade exata: mascara deve ser removida antes
    assert EmpresaRepository(session).get_by_cnpj("12.345.678/9012-34") is None


# ----------------------------------------------------------------------
# GET_ALL
# ----------------------------------------------------------------------

def test_get_all_retorna_seeds(session):
    empresas = EmpresaRepository(session).get_all()

    assert {CNPJ_SEED_1, CNPJ_SEED_2} <= {e.cnpj for e in empresas}


def test_get_all_inclui_recem_criada(session):
    repo = EmpresaRepository(session)
    criada = repo.create(Empresa(**empresa_request))

    assert criada.id in {e.id for e in repo.get_all()}


# ----------------------------------------------------------------------
# UPDATE
# ----------------------------------------------------------------------

def test_update(session):
    repo = EmpresaRepository(session)
    empresa = repo.get_by_cnpj(CNPJ_SEED_1)
    dados = {"nome": "Nome Update", "usuario": "usuario_update", "senha": "nova"}

    resultado = aplicar(repo, empresa, dados)

    assert campos(resultado, dados) == dados
    assert resultado.cnpj == CNPJ_SEED_1  # nao mexeu


def test_update_apenas_nome(session):
    repo = EmpresaRepository(session)

    resultado = aplicar(repo, repo.get_by_cnpj(CNPJ_SEED_1), {"nome": "So Nome"})

    assert resultado.nome == "So Nome"
    assert resultado.usuario == USUARIO_SEED_1


def test_update_persiste_no_banco(session):
    repo = EmpresaRepository(session)
    aplicar(repo, repo.get_by_cnpj(CNPJ_SEED_1), {"nome": "Persistido"})

    session.expire_all()

    assert repo.get_by_cnpj(CNPJ_SEED_1).nome == "Persistido"


def test_update_cnpj_duplicado(session):
    repo = EmpresaRepository(session)

    with pytest.raises(IntegrityError):
        aplicar(repo, repo.get_by_cnpj(CNPJ_SEED_1), {"cnpj": CNPJ_SEED_2})


def test_update_para_o_proprio_cnpj(session):
    repo = EmpresaRepository(session)

    resultado = aplicar(repo, repo.get_by_cnpj(CNPJ_SEED_1), {"cnpj": CNPJ_SEED_1})

    assert resultado.cnpj == CNPJ_SEED_1


def test_update_usuario_duplicado(session):
    repo = EmpresaRepository(session)

    with pytest.raises(IntegrityError):
        aplicar(repo, repo.get_by_cnpj(CNPJ_SEED_1), {"usuario": USUARIO_SEED_2})


def test_update_para_o_proprio_usuario(session):
    repo = EmpresaRepository(session)

    resultado = aplicar(
        repo, repo.get_by_cnpj(CNPJ_SEED_1), {"usuario": USUARIO_SEED_1}
    )

    assert resultado.usuario == USUARIO_SEED_1


@pytest.mark.parametrize("campo", CAMPOS)
def test_update_campo_obrigatorio_nulo(session, campo):
    repo = EmpresaRepository(session)

    with pytest.raises(IntegrityError):
        aplicar(repo, repo.get_by_cnpj(CNPJ_SEED_1), {campo: None})


def test_update_nome_acima_do_limite(session):
    repo = EmpresaRepository(session)

    with pytest.raises(DataError):
        aplicar(repo, repo.get_by_cnpj(CNPJ_SEED_1), {"nome": "x" * 101})
