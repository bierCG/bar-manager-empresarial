from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.core.exceptions.errors import CNPJDuplicado, EmpresaNaoEncontrada
from app.repositories.empresas import EmpresaRepository
from app.schemas.empresa import (
    CreateRequestEmpresa,
    CreateResponseEmpresa,
    UpdateRequestEmpresa,
)
from app.services import empresas as modulo  # ajuste o caminho se for outro
from app.services.empresas import EmpresaService

CNPJ_VALIDO = "11.222.333/0001-81"
CNPJ_VALIDO_SO_DIGITOS = "11222333000181"


# ---------- fixtures e helpers ----------

@pytest.fixture
def service():
    """Service com o repositório trocado por um mock (sem banco de dados).

    spec=EmpresaRepository faz o mock aceitar SÓ métodos que existem de verdade
    no repositório. Assim, chamar um método com nome errado quebra o teste.
    """
    svc = EmpresaService(session=MagicMock())
    svc.repo = MagicMock(spec=EmpresaRepository)
    return svc


def _cadastro(**extra):
    dados = {
        "nome": "Bar do Zé",
        "cnpj": CNPJ_VALIDO,
        "usuario": "barze",
        "senha": "1234",
    }
    dados.update(extra)
    return CreateRequestEmpresa(**dados)


# ---------- cadastrar ----------

def test_cadastrar_cnpj_duplicado(service):
    service.repo.get_by_cnpj.return_value = SimpleNamespace(id=1)

    with pytest.raises(CNPJDuplicado):
        service.cadastrar(_cadastro())

    service.repo.create.assert_not_called()


def test_cadastrar_consulta_cnpj_normalizado(service, monkeypatch):
    monkeypatch.setattr(modulo, "hash_senha", lambda s: f"hash:{s}")
    monkeypatch.setattr(modulo, "Empresa", lambda **kw: SimpleNamespace(**kw))
    service.repo.get_by_cnpj.return_value = None

    service.cadastrar(_cadastro())

    # o schema tira pontos e barras antes de chegar ao service
    service.repo.get_by_cnpj.assert_called_once_with(CNPJ_VALIDO_SO_DIGITOS)


def test_cadastrar_salva_hash_e_nao_a_senha_pura(service, monkeypatch):
    monkeypatch.setattr(modulo, "hash_senha", lambda s: f"hash:{s}")
    monkeypatch.setattr(modulo, "Empresa", lambda **kw: SimpleNamespace(**kw))
    service.repo.get_by_cnpj.return_value = None

    resultado = service.cadastrar(_cadastro())

    empresa_criada = service.repo.create.call_args[0][0]
    assert empresa_criada.senha == "hash:1234"
    assert empresa_criada.senha != "1234"
    assert empresa_criada.nome == "Bar do Zé"
    assert empresa_criada.usuario == "barze"
    assert empresa_criada.cnpj == CNPJ_VALIDO_SO_DIGITOS
    assert resultado == service.repo.create.return_value


# ---------- atualizar_cadastro ----------

def test_atualizar_empresa_nao_encontrada(service):
    service.repo.get_by_id.return_value = None

    with pytest.raises(EmpresaNaoEncontrada):
        service.atualizar_cadastro(UpdateRequestEmpresa(nome="Novo Nome"), empresa_id=99)

    service.repo.update.assert_not_called()


def test_atualizar_busca_por_id(service):
    service.repo.get_by_id.return_value = SimpleNamespace(nome="Antigo")

    service.atualizar_cadastro(UpdateRequestEmpresa(nome="Novo Nome"), empresa_id=42)

    service.repo.get_by_id.assert_called_once_with(42)


def test_atualizar_altera_nome_e_salva(service):
    empresa = SimpleNamespace(nome="Antigo", cnpj=CNPJ_VALIDO_SO_DIGITOS)
    service.repo.get_by_id.return_value = empresa

    resultado = service.atualizar_cadastro(UpdateRequestEmpresa(nome="Novo Nome"), empresa_id=1)

    assert empresa.nome == "Novo Nome"
    assert empresa.cnpj == CNPJ_VALIDO_SO_DIGITOS  # não enviado, não pode mudar
    service.repo.update.assert_called_once_with(empresa)
    assert resultado == service.repo.update.return_value


# ---------- listar_empresas ----------

def test_listar_empresas(service):
    resultado = service.listar_empresas()

    service.repo.get_all.assert_called_once_with()
    assert resultado == service.repo.get_all.return_value


# ---------- schema: CNPJ ----------

def test_cnpj_valido_e_normalizado():
    assert _cadastro().cnpj == CNPJ_VALIDO_SO_DIGITOS


def test_cnpj_so_digitos_tambem_vale():
    assert _cadastro(cnpj=CNPJ_VALIDO_SO_DIGITOS).cnpj == CNPJ_VALIDO_SO_DIGITOS


@pytest.mark.parametrize(
    "cnpj",
    [
        "11222333000182",      # dígito verificador errado
        "11111111111111",      # todos os dígitos iguais
        "123",                 # curto demais
        "112223330001811",     # longo demais
        "abcdefghijklmn",      # sem dígitos
        "",
    ],
)
def test_cnpj_invalido(cnpj):
    with pytest.raises(ValidationError):
        _cadastro(cnpj=cnpj)


# ---------- schema: demais regras do cadastro ----------

@pytest.mark.parametrize(
    "campo, valor",
    [
        ("nome", "abc"),
        ("usuario", "abc"),
        ("senha", "abc"),
    ],
)
def test_cadastro_campos_com_minimo_de_4(campo, valor):
    with pytest.raises(ValidationError):
        _cadastro(**{campo: valor})


# ---------- schema: update ----------

def test_update_valido():
    assert UpdateRequestEmpresa(nome="Novo Nome").nome == "Novo Nome"


def test_update_nome_curto_invalido():
    with pytest.raises(ValidationError):
        UpdateRequestEmpresa(nome="abc")


# ---------- schema: resposta NÃO pode expor a senha ----------

def test_resposta_nao_tem_campo_senha():
    assert "senha" not in CreateResponseEmpresa.model_fields


def test_resposta_nao_devolve_hash_da_senha():
    empresa_do_banco = SimpleNamespace(
        nome="Bar do Zé",
        cnpj=CNPJ_VALIDO_SO_DIGITOS,
        usuario="barze",
        senha="$2b$12$hash-secreto",
    )

    resposta = CreateResponseEmpresa.model_validate(empresa_do_banco).model_dump()

    assert "senha" not in resposta
    assert resposta == {
        "nome": "Bar do Zé",
        "cnpj": CNPJ_VALIDO_SO_DIGITOS,
        "usuario": "barze",
    }
