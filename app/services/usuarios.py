from enum import StrEnum

from sqlalchemy.orm import Session

from app.core.database.models import Usuario
from app.core.exceptions.errors import (
    RoleDesconhecida,
    UsuarioDuplicado,
    UsuarioNaoEncontrado
) 
from app.core.security.password import hash_senha
from app.repositories.usuarios import UsuarioRepository
from app.schemas.usuario import CreateRequest, UpdateRequest


class Role(StrEnum):
    BARTENDER = "bartender"
    COZINHA = "cozinha"
    EXPOSITOR = "expositor"


class UsuarioService():
    def __init__(self, session: Session):
        self.repo = UsuarioRepository(session)

    def cadastrar(self, cadastro: CreateRequest, empresa_id: int) -> Usuario:
        self._validar_role(cadastro.role)
        self._garantir_username_disponivel(cadastro.usuario, empresa_id)

        usuario = Usuario(
            **cadastro.model_dump(exclude={"senha"}),
            senha_hash=hash_senha(cadastro.senha),
            empresa_id=empresa_id
        )
        return self.repo.create(usuario)

    def atualizar_cadastro(
        self, dados: UpdateRequest, usuario_id: int, empresa_id: int
    ) -> Usuario:
        usuario = self.repo.get_by_id(usuario_id, empresa_id)
        if not usuario:
            raise UsuarioNaoEncontrado()

        campos = dados.model_dump(exclude_none=True)

        if "role" in campos:
            self._validar_role(campos["role"])

        if "usuario" in campos:
            self._garantir_username_disponivel(
                campos["usuario"], empresa_id, ignorar_id=usuario_id
            )

        if "senha" in campos:
            campos["senha_hash"] = hash_senha(campos.pop("senha"))

        for campo, valor in campos.items():
            setattr(usuario, campo, valor)

        return self.repo.update(usuario)

    def listar_usuarios(self, empresa_id: int) -> list[Usuario]:
        return self.repo.get_usuarios_empresa(empresa_id)

    @staticmethod
    def _validar_role(role: str) -> None:
        if role not in {r.value for r in Role}:
            raise RoleDesconhecida()

    def _garantir_username_disponivel(
        self, username: str, empresa_id: int, ignorar_id: int | None = None
    ) -> None:
        existente = self.repo.get_by_username(username, empresa_id)
        if existente and existente.id != ignorar_id:
            raise UsuarioDuplicado()