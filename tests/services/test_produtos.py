from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.core.exceptions.errors import ProdutoNaoEncontrado
from app.schemas.produto import CreateRequest, UpdateRequest
from app.services import produtos as modulo  # ajuste o caminho se for outro
from app.services.produtos import ProdutoService


# ---------- fixtures ----------

@pytest.fixture
def service():
    """Service com o repositório trocado por um mock (sem banco de dados)."""
    svc = ProdutoService(session=MagicMock())
    svc.repo = MagicMock()
    return svc


def _produto(nome="Cerveja", valor=10.0):
    # objeto simples: aceita setattr e permite conferir os valores depois
    return SimpleNamespace(nome=nome, valor=valor)


# ---------- cadastrar_produto ----------

def test_cadastrar_produto_usa_dados_e_empresa(service, monkeypatch):
    class ProdutoFalso:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    monkeypatch.setattr(modulo, "Produto", ProdutoFalso)

    cadastro = MagicMock()
    cadastro.model_dump.return_value = {"nome": "Cerveja", "valor": 12.5}

    resultado = service.cadastrar_produto(cadastro, empresa_id=9)

    produto_criado = service.repo.create.call_args[0][0]
    assert produto_criado.nome == "Cerveja"
    assert produto_criado.valor == 12.5
    assert produto_criado.empresa_id == 9
    assert resultado == service.repo.create.return_value


# ---------- atualizar_cadastro ----------

def test_atualizar_produto_nao_encontrado(service):
    service.repo.get_produto.return_value = None

    with pytest.raises(ProdutoNaoEncontrado):
        service.atualizar_cadastro(UpdateRequest(valor=5), produto_id=1, empresa_id=1)

    service.repo.update.assert_not_called()


def test_atualizar_consulta_com_ids_corretos(service):
    service.repo.get_produto.return_value = _produto()

    service.atualizar_cadastro(UpdateRequest(valor=5), produto_id=10, empresa_id=20)

    service.repo.get_produto.assert_called_once_with(10, 20)


def test_atualizar_so_altera_campos_enviados(service):
    produto = _produto(nome="Cerveja", valor=10.0)
    service.repo.get_produto.return_value = produto

    service.atualizar_cadastro(UpdateRequest(valor=15.0), produto_id=1, empresa_id=1)

    assert produto.valor == 15.0
    assert produto.nome == "Cerveja"  # não enviado, não pode mudar
    service.repo.update.assert_called_once_with(produto)


def test_atualizar_varios_campos(service):
    produto = _produto()
    service.repo.get_produto.return_value = produto

    service.atualizar_cadastro(UpdateRequest(nome="Chopp", valor=8.0), produto_id=1, empresa_id=1)

    assert produto.nome == "Chopp"
    assert produto.valor == 8.0


def test_atualizar_ignora_campo_null(service):
    produto = _produto(nome="Cerveja")
    service.repo.get_produto.return_value = produto

    service.atualizar_cadastro(UpdateRequest(nome=None), produto_id=1, empresa_id=1)

    assert produto.nome == "Cerveja"  # null não pode apagar o nome


# ---------- listar_produtos ----------

def test_listar_produtos_repassa_empresa_e_resultado(service):
    resultado = service.listar_produtos(empresa_id=3)

    service.repo.get_all.assert_called_once_with(3)
    assert resultado == service.repo.get_all.return_value


# ---------- validação dos schemas ----------

def test_create_valido():
    produto = CreateRequest(nome="Cerveja", valor=10)
    assert produto.nome == "Cerveja"
    assert produto.valor == 10


@pytest.mark.parametrize(
    "dados",
    [
        {"nome": "abc", "valor": 10},      # nome com menos de 4 caracteres
        {"nome": "Cerveja", "valor": 0},   # valor deve ser maior que 0
        {"nome": "Cerveja", "valor": -1},
        {"valor": 10},                      # nome obrigatório
        {"nome": "Cerveja"},                # valor obrigatório
    ],
)
def test_create_invalido(dados):
    with pytest.raises(ValidationError):
        CreateRequest(**dados)


def test_update_aceita_vazio_e_parcial():
    assert UpdateRequest().model_dump(exclude_unset=True) == {}
    assert UpdateRequest(valor=5).model_dump(exclude_unset=True) == {"valor": 5}


@pytest.mark.parametrize(
    "dados",
    [
        {"nome": "abc"},   # mesma regra do cadastro
        {"valor": 0},
        {"valor": -5},
    ],
)
def test_update_invalido(dados):
    with pytest.raises(ValidationError):
        UpdateRequest(**dados)
