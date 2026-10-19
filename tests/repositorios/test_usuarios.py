import pytest
from sqlalchemy.exc import IntegrityError

from app.core.database.models import Usuario
from app.repositories.usuarios import UsuarioRepository

EMPRESA = 1

create_request = {
    "nome": "Nome Teste",
    "usuario": "Username Teste",
    "role": "Role Teste",
    "senha_hash": "Senha Teste",
}


def campos(obj, esperado):
    """Extrai de obj apenas as chaves de `esperado`, para comparar dicts."""
    return {k: getattr(obj, k) for k in esperado}


def aplicar(repo, usuario_id, empresa_id, dados):
    usuario = repo.get_by_id(usuario_id, empresa_id)
    for campo, valor in dados.items():
        setattr(usuario, campo, valor)
    return repo.update(usuario)


# ----------------------------------------------------------------------
# CREATE
# ----------------------------------------------------------------------

def test_create(session):
    esperado = {**create_request, "empresa_id": EMPRESA}

    resultado = UsuarioRepository(session).create(
        Usuario(**create_request, empresa_id=EMPRESA)
    )

    assert resultado.id is not None
    assert campos(resultado, esperado) == esperado


def test_create_persiste_no_banco(session):
    repo = UsuarioRepository(session)
    criado = repo.create(Usuario(**create_request, empresa_id=EMPRESA))

    session.expire_all() 

    buscado = repo.get_by_id(criado.id, EMPRESA)
    assert buscado is not None
    assert buscado.usuario == create_request["usuario"]


def test_create_username_duplicado(session):
    dados = {**create_request, "usuario": "usuario1"}  # SEEDS

    with pytest.raises(IntegrityError):
        UsuarioRepository(session).create(Usuario(**dados, empresa_id=EMPRESA))


def test_create_empresa_inexistente(session):
    with pytest.raises(IntegrityError):
        UsuarioRepository(session).create(
            Usuario(**create_request, empresa_id=1000)
        )


@pytest.mark.parametrize("campo", ["nome", "usuario", "role", "senha_hash"])
def test_create_campo_obrigatorio_nulo(session, campo):
    dados = {**create_request, campo: None}

    with pytest.raises(IntegrityError):
        UsuarioRepository(session).create(Usuario(**dados, empresa_id=EMPRESA))


def test_create_sem_empresa_id(session):
    with pytest.raises(IntegrityError):
        UsuarioRepository(session).create(Usuario(**create_request))


# ----------------------------------------------------------------------
# GET_BY_ID
# ----------------------------------------------------------------------

def test_get_by_id(session):
    usuario = UsuarioRepository(session).get_by_id(1, EMPRESA)

    assert usuario is not None
    assert usuario.id == 1
    assert usuario.empresa_id == EMPRESA


def test_get_by_id_inexistente(session):
    assert UsuarioRepository(session).get_by_id(9999, EMPRESA) is None


def test_get_by_id_outra_empresa(session):
    assert UsuarioRepository(session).get_by_id(1, 2) is None


# ----------------------------------------------------------------------
# GET_BY_USERNAME
# ----------------------------------------------------------------------

def test_get_by_username(session):
    usuario = UsuarioRepository(session).get_by_username("usuario1", EMPRESA)

    assert usuario is not None
    assert usuario.usuario == "usuario1"
    assert usuario.empresa_id == EMPRESA


def test_get_by_username_inexistente(session):
    assert UsuarioRepository(session).get_by_username("nao_existe", EMPRESA) is None


def test_get_by_username_outra_empresa(session):
    assert UsuarioRepository(session).get_by_username("usuario1", 2) is None


# ----------------------------------------------------------------------
# GET_USUARIOS_EMPRESA
# ----------------------------------------------------------------------

def test_get_usuarios_empresa(session):
    usuarios = UsuarioRepository(session).get_usuarios_empresa(EMPRESA)

    assert len(usuarios) >= 2
    assert all(u.empresa_id == EMPRESA for u in usuarios)
    nomes_usuario = {u.usuario for u in usuarios}
    assert {"usuario1", "usuario2"} <= nomes_usuario


def test_get_usuarios_empresa_sem_usuarios(session):
    assert UsuarioRepository(session).get_usuarios_empresa(9999) == []


def test_get_usuarios_empresa_inclui_recem_criado(session):
    repo = UsuarioRepository(session)
    repo.create(Usuario(**create_request, empresa_id=EMPRESA))

    usuarios = repo.get_usuarios_empresa(EMPRESA)

    assert create_request["usuario"] in {u.usuario for u in usuarios}


# ----------------------------------------------------------------------
# UPDATE
# ----------------------------------------------------------------------

def test_update(session):
    dados = {"nome": "Nome Update", "usuario": "Username Update"}

    resultado = aplicar(UsuarioRepository(session), 1, EMPRESA, dados)

    assert campos(resultado, dados) == dados


def test_update_apenas_nome(session):
    resultado = aplicar(UsuarioRepository(session), 1, EMPRESA, {"nome": "Update Nome"})

    assert resultado.nome == "Update Nome"
    assert resultado.usuario == "usuario1"  # não mexeu


def test_update_apenas_username(session):
    resultado = aplicar(
        UsuarioRepository(session), 1, EMPRESA, {"usuario": "Update Username"}
    )

    assert resultado.usuario == "Update Username"
    assert resultado.nome == "Usuario 1"  # não mexeu


def test_update_persiste_no_banco(session):
    repo = UsuarioRepository(session)
    aplicar(repo, 1, EMPRESA, {"nome": "Persistido"})

    session.expire_all()

    assert repo.get_by_id(1, EMPRESA).nome == "Persistido"


def test_update_username_duplicado(session):
    with pytest.raises(IntegrityError):
        aplicar(UsuarioRepository(session), 1, EMPRESA, {"usuario": "usuario2"})  # SEEDS


def test_update_para_o_proprio_username(session):
    resultado = aplicar(UsuarioRepository(session), 1, EMPRESA, {"usuario": "usuario1"})

    assert resultado.usuario == "usuario1"


def test_update_empresa_inexistente(session):
    with pytest.raises(IntegrityError):
        aplicar(UsuarioRepository(session), 1, EMPRESA, {"empresa_id": 1000})


@pytest.mark.parametrize("campo", ["nome", "usuario", "role", "senha_hash"])
def test_update_campo_obrigatorio_nulo(session, campo):
    with pytest.raises(IntegrityError):
        aplicar(UsuarioRepository(session), 1, EMPRESA, {campo: None})