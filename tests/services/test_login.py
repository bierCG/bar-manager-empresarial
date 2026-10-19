from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.exceptions.errors import LoginInvalido
from app.repositories.empresas import EmpresaRepository
from app.repositories.usuarios import UsuarioRepository
from app.services import login as modulo  # ajuste o caminho se for outro
from app.services.login import LoginService
from app.schemas.login import LoginRequest


# ---------- fixtures e helpers ----------

@pytest.fixture
def tokens(monkeypatch):
    """Troca create_token por uma função falsa que guarda o payload recebido."""
    capturado = {"chamadas": 0, "payload": None}

    def create_token_falso(payload):
        capturado["chamadas"] += 1
        capturado["payload"] = payload
        return "token-falso"

    monkeypatch.setattr(modulo, "create_token", create_token_falso)
    return capturado


@pytest.fixture(autouse=True)
def configuracao(monkeypatch):
    """Senhas de teste: o 'hash' de uma senha X é o texto 'hash:X'."""
    monkeypatch.setattr(
        modulo, "validar_senha", lambda senha, hash_: hash_ == f"hash:{senha}"
    )
    monkeypatch.setattr(
        modulo,
        "settings",
        SimpleNamespace(ADMIN_USUARIO="admin", ADMIN_SENHA_HASH="hash:segredo"),
    )


@pytest.fixture
def service():
    """Service com os repositórios trocados por mocks (sem banco de dados).

    spec=... faz o mock aceitar SÓ métodos que existem de verdade no repositório.
    """
    svc = LoginService(session=MagicMock())
    svc.usuario_repo = MagicMock(spec=UsuarioRepository)
    svc.empresa_repo = MagicMock(spec=EmpresaRepository)
    return svc


def _login(usuario, senha):
    return SimpleNamespace(usuario=usuario, senha=senha)


def _assert_expira_em_12h(payload, antes, depois):
    assert antes + timedelta(hours=12) <= payload["exp"] <= depois + timedelta(hours=12)


# ---------- logar_admin ----------

def test_admin_ok(service, tokens):
    antes = datetime.now(timezone.utc)

    resultado = service.logar_admin(_login("admin", "segredo"))

    depois = datetime.now(timezone.utc)
    assert resultado == {"access_token": "token-falso"}
    assert tokens["payload"]["sub"] == "admin"
    assert tokens["payload"]["role"] == "admin"
    _assert_expira_em_12h(tokens["payload"], antes, depois)


@pytest.mark.parametrize(
    "usuario, senha",
    [
        ("outro", "segredo"),   # usuário errado
        ("admin", "errada"),    # senha errada
        ("outro", "errada"),    # os dois errados
        ("", ""),
    ],
)
def test_admin_credenciais_invalidas(service, tokens, usuario, senha):
    with pytest.raises(LoginInvalido):
        service.logar_admin(_login(usuario, senha))

    assert tokens["chamadas"] == 0  # nenhum token pode ser gerado


def test_admin_usuario_com_acento_nao_quebra(service, tokens):
    # antes: compare_digest com str não-ASCII lançava TypeError (erro 500)
    with pytest.raises(LoginInvalido):
        service.logar_admin(_login("adminé", "segredo"))


# ---------- logar_usuario ----------

def _usuario(**extra):
    dados = dict(id=7, role="bartender", empresa_id=3, senha_hash="hash:1234")
    dados.update(extra)
    return SimpleNamespace(**dados)


def test_usuario_ok(service, tokens):
    service.usuario_repo.get_by_username.return_value = _usuario()
    antes = datetime.now(timezone.utc)

    resultado = service.logar_usuario(_login("joao", "1234"))

    depois = datetime.now(timezone.utc)
    assert resultado == {"access_token": "token-falso"}
    assert tokens["payload"]["sub"] == "7"          # sub sempre como texto
    assert tokens["payload"]["role"] == "bartender"
    assert tokens["payload"]["empresa"] == 3
    _assert_expira_em_12h(tokens["payload"], antes, depois)
    service.usuario_repo.get_by_username.assert_called_once_with("joao")


def test_usuario_inexistente(service, tokens):
    service.usuario_repo.get_by_username.return_value = None

    with pytest.raises(LoginInvalido):
        service.logar_usuario(_login("fantasma", "1234"))

    assert tokens["chamadas"] == 0


def test_usuario_senha_errada(service, tokens):
    service.usuario_repo.get_by_username.return_value = _usuario()

    with pytest.raises(LoginInvalido):
        service.logar_usuario(_login("joao", "errada"))

    assert tokens["chamadas"] == 0


# ---------- logar_empresa ----------

def _empresa(**extra):
    dados = dict(id=5, senha="hash:1234")
    dados.update(extra)
    return SimpleNamespace(**dados)


def test_empresa_ok(service, tokens):
    service.empresa_repo.get_by_username.return_value = _empresa()
    antes = datetime.now(timezone.utc)
    
    resultado = service.logar_empresa(LoginRequest(usuario="barze", senha="1234"))

    depois = datetime.now(timezone.utc)
    assert resultado == {"access_token": "token-falso"}
    assert tokens["payload"]["sub"] == "5"
    assert tokens["payload"]["role"] == "empresa"
    assert "empresa" not in tokens["payload"]
    _assert_expira_em_12h(tokens["payload"], antes, depois)
    service.empresa_repo.get_by_username.assert_called_once_with("barze")


def test_empresa_inexistente(service, tokens):
    service.empresa_repo.get_by_username.return_value = None

    with pytest.raises(LoginInvalido):
        service.logar_empresa(LoginRequest(usuario="fantasma", senha="1234"))

    assert tokens["chamadas"] == 0


def test_empresa_senha_errada(service, tokens):
    service.empresa_repo.get_by_username.return_value = _empresa()

    with pytest.raises(LoginInvalido):
        service.logar_empresa(LoginRequest(usuario="barze", senha="errada"))

    assert tokens["chamadas"] == 0


# ---------- um login não usa o repositório do outro ----------

def test_logins_usam_repositorios_separados(service, tokens):
    service.usuario_repo.get_by_username.return_value = _usuario()

    service.logar_usuario(_login("joao", "1234"))

    service.empresa_repo.get_by_username.assert_not_called()
