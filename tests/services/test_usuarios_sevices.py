"""Testes unitários da camada de service: UsuarioService.

Estratégia de isolamento
------------------------
* ``UsuarioRepository`` é substituído por um mock com ``autospec=True``. Assim
  qualquer chamada com assinatura errada (ex.: esquecer ``empresa_id``) falha
  no teste, em vez de passar silenciosamente.
* ``hash_senha`` também é substituído (``autospec=True``), mantendo os testes
  rápidos e determinísticos.
* O model ``Usuario`` e os schemas Pydantic são reais: queremos validar que o
  service monta o model com os campos corretos e que o ``setattr`` do update
  atinge colunas que existem.
* Nenhum teste acessa banco de dados.

Ajuste ``MODULO`` caso o service esteja em outro caminho do projeto.
"""

import pytest
from sqlalchemy.orm import Session

from app.core.database.models import Usuario
from app.core.exceptions.errors import (
    RoleDesconhecida,
    UsuarioDuplicado,
    UsuarioNaoEncontrado,
)
from app.schemas.usuario import CreateRequest, UpdateRequest
from app.services.usuarios import Role, UsuarioService

MODULO = "app.services.usuarios"

EMPRESA_ID = 10
USUARIO_ID = 1
HASH_GERADO = "hash-gerado"
HASH_ANTIGO = "hash-antigo"

ROLES_VALIDAS = ["bartender", "cozinha", "expositor"]
ROLES_INVALIDAS = ["admin", "", "BARTENDER", "Cozinha", " expositor", "bartender "]


# --------------------------------------------------------------------------- #
# Fixtures e helpers
# --------------------------------------------------------------------------- #
@pytest.fixture
def session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def repo_cls(mocker):
    return mocker.patch(f"{MODULO}.UsuarioRepository", autospec=True)


@pytest.fixture
def repo(repo_cls):
    """Instância mockada do repositório.

    Por padrão: nenhum usuário com o username buscado e nenhum usuário com o id
    buscado. Cada teste sobrescreve o que precisar.
    """
    instancia = repo_cls.return_value
    instancia.get_by_username.return_value = None
    instancia.get_by_id.return_value = None
    return instancia


@pytest.fixture
def hash_senha_mock(mocker):
    return mocker.patch(
        f"{MODULO}.hash_senha", autospec=True, return_value=HASH_GERADO
    )


@pytest.fixture
def service(session, repo):
    return UsuarioService(session)


def _cadastro(**overrides) -> CreateRequest:
    dados = {
        "nome": "Maria Silva",
        "usuario": "maria",
        "senha": "senha-em-texto-puro",
        "role": "bartender",
    }
    dados.update(overrides)
    return CreateRequest(**dados)


def _usuario_existente(**overrides) -> Usuario:
    dados = {
        "id": USUARIO_ID,
        "nome": "Maria Silva",
        "usuario": "maria",
        "senha_hash": HASH_ANTIGO,
        "role": "bartender",
        "empresa_id": EMPRESA_ID,
    }
    dados.update(overrides)
    return Usuario(**dados)


# --------------------------------------------------------------------------- #
# Role
# --------------------------------------------------------------------------- #
class TestRole:
    def test_roles_do_enum_sao_as_esperadas(self):
        assert {r.value for r in Role} == set(ROLES_VALIDAS)


# --------------------------------------------------------------------------- #
# Construção
# --------------------------------------------------------------------------- #
class TestInit:
    def test_instancia_repositorio_com_a_session_recebida(self, repo_cls, session):
        service = UsuarioService(session)

        repo_cls.assert_called_once_with(session)
        assert service.repo is repo_cls.return_value


# --------------------------------------------------------------------------- #
# cadastrar
# --------------------------------------------------------------------------- #
class TestCadastrar:
    def test_cadastra_usuario_com_sucesso(self, service, repo, hash_senha_mock):
        cadastro = _cadastro()

        service.cadastrar(cadastro, EMPRESA_ID)

        repo.create.assert_called_once()
        criado = repo.create.call_args.args[0]
        assert isinstance(criado, Usuario)
        assert criado.nome == cadastro.nome
        assert criado.usuario == cadastro.usuario
        assert criado.role == cadastro.role
        assert criado.empresa_id == EMPRESA_ID

    def test_retorna_o_que_o_repositorio_devolve(
        self, service, repo, hash_senha_mock, mocker
    ):
        persistido = mocker.sentinel.usuario_persistido
        repo.create.return_value = persistido

        resultado = service.cadastrar(_cadastro(), EMPRESA_ID)

        assert resultado is persistido

    def test_senha_e_hasheada_e_nunca_persistida_em_texto_puro(
        self, service, repo, hash_senha_mock
    ):
        cadastro = _cadastro(senha="minha-senha-secreta")

        service.cadastrar(cadastro, EMPRESA_ID)

        hash_senha_mock.assert_called_once_with("minha-senha-secreta")
        criado = repo.create.call_args.args[0]
        assert criado.senha_hash == HASH_GERADO
        assert criado.senha_hash != "minha-senha-secreta"

    def test_verifica_username_no_escopo_da_empresa(
        self, service, repo, hash_senha_mock
    ):
        service.cadastrar(_cadastro(usuario="maria"), EMPRESA_ID)

        repo.get_by_username.assert_called_once_with("maria", EMPRESA_ID)

    @pytest.mark.parametrize("role", ROLES_VALIDAS)
    def test_aceita_cada_role_valida(self, service, repo, hash_senha_mock, role):
        service.cadastrar(_cadastro(role=role), EMPRESA_ID)

        criado = repo.create.call_args.args[0]
        assert criado.role == role

    def test_username_duplicado_levanta_erro_e_nao_persiste(
        self, service, repo, hash_senha_mock
    ):
        repo.get_by_username.return_value = _usuario_existente()

        with pytest.raises(UsuarioDuplicado):
            service.cadastrar(_cadastro(), EMPRESA_ID)

        repo.create.assert_not_called()
        hash_senha_mock.assert_not_called()

    @pytest.mark.parametrize("role", ROLES_INVALIDAS)
    def test_role_invalida_levanta_erro_e_nao_persiste(
        self, service, repo, hash_senha_mock, role
    ):
        with pytest.raises(RoleDesconhecida):
            service.cadastrar(_cadastro(role=role), EMPRESA_ID)

        repo.create.assert_not_called()

    def test_role_invalida_falha_antes_de_consultar_repo_ou_gerar_hash(
        self, service, repo, hash_senha_mock
    ):
        with pytest.raises(RoleDesconhecida):
            service.cadastrar(_cadastro(role="admin"), EMPRESA_ID)

        repo.get_by_username.assert_not_called()
        hash_senha_mock.assert_not_called()

    def test_role_invalida_tem_precedencia_sobre_username_duplicado(
        self, service, repo, hash_senha_mock
    ):
        repo.get_by_username.return_value = _usuario_existente()

        with pytest.raises(RoleDesconhecida):
            service.cadastrar(_cadastro(role="admin"), EMPRESA_ID)

    def test_erro_do_repositorio_na_criacao_e_propagado(
        self, service, repo, hash_senha_mock
    ):
        repo.create.side_effect = RuntimeError("falha no banco")

        with pytest.raises(RuntimeError, match="falha no banco"):
            service.cadastrar(_cadastro(), EMPRESA_ID)


# --------------------------------------------------------------------------- #
# atualizar_cadastro
# --------------------------------------------------------------------------- #
class TestAtualizarCadastro:
    # -- busca do usuário ---------------------------------------------------- #
    def test_busca_usuario_por_id_no_escopo_da_empresa(
        self, service, repo, hash_senha_mock
    ):
        repo.get_by_id.return_value = _usuario_existente()

        service.atualizar_cadastro(UpdateRequest(), USUARIO_ID, EMPRESA_ID)

        repo.get_by_id.assert_called_once_with(USUARIO_ID, EMPRESA_ID)

    def test_usuario_inexistente_levanta_erro_sem_efeitos_colaterais(
        self, service, repo, hash_senha_mock
    ):
        repo.get_by_id.return_value = None

        with pytest.raises(UsuarioNaoEncontrado):
            service.atualizar_cadastro(
                UpdateRequest(usuario="novo", senha="x", role="cozinha"),
                USUARIO_ID,
                EMPRESA_ID,
            )

        repo.get_by_username.assert_not_called()
        hash_senha_mock.assert_not_called()
        repo.update.assert_not_called()

    # -- atualização de campos ---------------------------------------------- #
    def test_retorna_o_que_o_repositorio_devolve(
        self, service, repo, hash_senha_mock, mocker
    ):
        repo.get_by_id.return_value = _usuario_existente()
        atualizado = mocker.sentinel.usuario_atualizado
        repo.update.return_value = atualizado

        resultado = service.atualizar_cadastro(
            UpdateRequest(role="cozinha"), USUARIO_ID, EMPRESA_ID
        )

        assert resultado is atualizado

    def test_atualiza_todos_os_campos_enviados(self, service, repo, hash_senha_mock):
        usuario = _usuario_existente()
        repo.get_by_id.return_value = usuario

        service.atualizar_cadastro(
            UpdateRequest(usuario="maria.nova", senha="nova-senha", role="cozinha"),
            USUARIO_ID,
            EMPRESA_ID,
        )

        assert usuario.usuario == "maria.nova"
        assert usuario.role == "cozinha"
        assert usuario.senha_hash == HASH_GERADO
        repo.update.assert_called_once_with(usuario)

    def test_atualizacao_parcial_preserva_campos_nao_enviados(
        self, service, repo, hash_senha_mock
    ):
        usuario = _usuario_existente()
        repo.get_by_id.return_value = usuario

        service.atualizar_cadastro(
            UpdateRequest(role="expositor"), USUARIO_ID, EMPRESA_ID
        )

        assert usuario.role == "expositor"
        assert usuario.usuario == "maria"
        assert usuario.nome == "Maria Silva"
        assert usuario.senha_hash == HASH_ANTIGO
        assert usuario.empresa_id == EMPRESA_ID
        assert usuario.id == USUARIO_ID

    def test_payload_vazio_nao_altera_nada_mas_persiste(
        self, service, repo, hash_senha_mock
    ):
        usuario = _usuario_existente()
        repo.get_by_id.return_value = usuario

        service.atualizar_cadastro(UpdateRequest(), USUARIO_ID, EMPRESA_ID)

        assert usuario.usuario == "maria"
        assert usuario.role == "bartender"
        assert usuario.senha_hash == HASH_ANTIGO
        repo.get_by_username.assert_not_called()
        hash_senha_mock.assert_not_called()
        repo.update.assert_called_once_with(usuario)

    def test_campos_explicitamente_nulos_sao_ignorados(
        self, service, repo, hash_senha_mock
    ):
        usuario = _usuario_existente()
        repo.get_by_id.return_value = usuario

        service.atualizar_cadastro(
            UpdateRequest(usuario=None, senha=None, role="cozinha"),
            USUARIO_ID,
            EMPRESA_ID,
        )

        assert usuario.usuario == "maria"
        assert usuario.senha_hash == HASH_ANTIGO
        assert usuario.role == "cozinha"
        repo.get_by_username.assert_not_called()
        hash_senha_mock.assert_not_called()

    # -- senha --------------------------------------------------------------- #
    def test_senha_e_hasheada_e_gravada_em_senha_hash(
        self, service, repo, hash_senha_mock
    ):
        usuario = _usuario_existente()
        repo.get_by_id.return_value = usuario

        service.atualizar_cadastro(
            UpdateRequest(senha="nova-senha"), USUARIO_ID, EMPRESA_ID
        )

        hash_senha_mock.assert_called_once_with("nova-senha")
        assert usuario.senha_hash == HASH_GERADO
        assert not hasattr(usuario, "senha")

    def test_sem_senha_no_payload_hash_nao_e_gerado(
        self, service, repo, hash_senha_mock
    ):
        repo.get_by_id.return_value = _usuario_existente()

        service.atualizar_cadastro(
            UpdateRequest(role="cozinha"), USUARIO_ID, EMPRESA_ID
        )

        hash_senha_mock.assert_not_called()

    # -- username ------------------------------------------------------------ #
    def test_username_livre_e_aceito_e_consultado_no_escopo_da_empresa(
        self, service, repo, hash_senha_mock
    ):
        usuario = _usuario_existente()
        repo.get_by_id.return_value = usuario
        repo.get_by_username.return_value = None

        service.atualizar_cadastro(
            UpdateRequest(usuario="maria.nova"), USUARIO_ID, EMPRESA_ID
        )

        repo.get_by_username.assert_called_once_with("maria.nova", EMPRESA_ID)
        assert usuario.usuario == "maria.nova"

    def test_username_de_outro_usuario_levanta_erro_e_nao_altera_nada(
        self, service, repo, hash_senha_mock
    ):
        usuario = _usuario_existente()
        repo.get_by_id.return_value = usuario
        repo.get_by_username.return_value = _usuario_existente(id=99, usuario="joao")

        with pytest.raises(UsuarioDuplicado):
            service.atualizar_cadastro(
                UpdateRequest(usuario="joao"), USUARIO_ID, EMPRESA_ID
            )

        assert usuario.usuario == "maria"
        repo.update.assert_not_called()

    def test_reenviar_o_proprio_username_nao_e_duplicidade(
        self, service, repo, hash_senha_mock
    ):
        usuario = _usuario_existente()
        repo.get_by_id.return_value = usuario
        repo.get_by_username.return_value = usuario

        service.atualizar_cadastro(
            UpdateRequest(usuario="maria"), USUARIO_ID, EMPRESA_ID
        )

        repo.update.assert_called_once_with(usuario)

    # -- role ---------------------------------------------------------------- #
    @pytest.mark.parametrize("role", ROLES_VALIDAS)
    def test_aceita_cada_role_valida(self, service, repo, hash_senha_mock, role):
        usuario = _usuario_existente(role="bartender")
        repo.get_by_id.return_value = usuario

        service.atualizar_cadastro(UpdateRequest(role=role), USUARIO_ID, EMPRESA_ID)

        assert usuario.role == role

    @pytest.mark.parametrize("role", ROLES_INVALIDAS)
    def test_role_invalida_levanta_erro_e_nao_persiste(
        self, service, repo, hash_senha_mock, role
    ):
        usuario = _usuario_existente()
        repo.get_by_id.return_value = usuario

        with pytest.raises(RoleDesconhecida):
            service.atualizar_cadastro(
                UpdateRequest(role=role), USUARIO_ID, EMPRESA_ID
            )

        assert usuario.role == "bartender"
        repo.update.assert_not_called()

    def test_role_invalida_falha_antes_de_consultar_username_ou_gerar_hash(
        self, service, repo, hash_senha_mock
    ):
        repo.get_by_id.return_value = _usuario_existente()

        with pytest.raises(RoleDesconhecida):
            service.atualizar_cadastro(
                UpdateRequest(role="admin", usuario="novo", senha="x"),
                USUARIO_ID,
                EMPRESA_ID,
            )

        repo.get_by_username.assert_not_called()
        hash_senha_mock.assert_not_called()

    # -- atomicidade --------------------------------------------------------- #
    def test_falha_de_validacao_nao_deixa_o_model_parcialmente_alterado(
        self, service, repo, hash_senha_mock
    ):
        usuario = _usuario_existente()
        repo.get_by_id.return_value = usuario

        with pytest.raises(RoleDesconhecida):
            service.atualizar_cadastro(
                UpdateRequest(usuario="novo", senha="nova", role="admin"),
                USUARIO_ID,
                EMPRESA_ID,
            )

        assert usuario.usuario == "maria"
        assert usuario.senha_hash == HASH_ANTIGO
        assert usuario.role == "bartender"

    def test_erro_do_repositorio_no_update_e_propagado(
        self, service, repo, hash_senha_mock
    ):
        repo.get_by_id.return_value = _usuario_existente()
        repo.update.side_effect = RuntimeError("falha no banco")

        with pytest.raises(RuntimeError, match="falha no banco"):
            service.atualizar_cadastro(
                UpdateRequest(role="cozinha"), USUARIO_ID, EMPRESA_ID
            )


# --------------------------------------------------------------------------- #
# listar_usuarios
# --------------------------------------------------------------------------- #
class TestListarUsuarios:
    def test_delega_ao_repositorio_com_o_empresa_id(self, service, repo):
        repo.get_usuarios_empresa.return_value = []

        service.listar_usuarios(EMPRESA_ID)

        repo.get_usuarios_empresa.assert_called_once_with(EMPRESA_ID)

    def test_retorna_a_lista_do_repositorio(self, service, repo):
        usuarios = [_usuario_existente(id=1), _usuario_existente(id=2, usuario="joao")]
        repo.get_usuarios_empresa.return_value = usuarios

        assert service.listar_usuarios(EMPRESA_ID) == usuarios

    def test_retorna_lista_vazia_quando_empresa_nao_tem_usuarios(self, service, repo):
        repo.get_usuarios_empresa.return_value = []

        assert service.listar_usuarios(EMPRESA_ID) == []
