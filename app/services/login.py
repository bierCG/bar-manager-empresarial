import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.exceptions.errors import LoginInvalido
from app.core.security.auth import create_token
from app.core.security.password import validar_senha
from app.core.settings import settings
from app.repositories.empresas import EmpresaRepository
from app.repositories.usuarios import UsuarioRepository
from app.schemas.login import LoginRequest

TOKEN_VALIDADE = timedelta(hours=12)

class LoginService:
    def __init__(self, session: Session):
        self.usuario_repo = UsuarioRepository(session)
        self.empresa_repo = EmpresaRepository(session)

    @staticmethod
    def _gerar_token(payload: dict) -> dict[str, str]:
        payload = {**payload, "exp": datetime.now(timezone.utc) + TOKEN_VALIDADE}
        return {"access_token": create_token(payload)}

    def logar_admin(self, login: LoginRequest) -> dict[str, str]:
        usuario_ok = secrets.compare_digest(
            login.usuario.encode(), settings.ADMIN_USUARIO.encode()
        )
        senha_ok = validar_senha(login.senha, settings.ADMIN_SENHA_HASH)

        if not (usuario_ok and senha_ok):
            raise LoginInvalido()

        return self._gerar_token({"sub": "admin", "role": "admin"})

    def logar_usuario(self, login: LoginRequest) -> dict[str, str]:
        usuario = self.usuario_repo.get_by_username(login.usuario)

        if not usuario or not validar_senha(login.senha, usuario.senha_hash):
            raise LoginInvalido()

        return self._gerar_token(
            {
                "sub": str(usuario.id),
                "role": usuario.role,
                "empresa": usuario.empresa_id,
            }
        )

    def logar_empresa(self, login: LoginRequest) -> dict[str, str]:
        empresa = self.empresa_repo.get_by_username(login.usuario)

        if not empresa or not validar_senha(login.senha, empresa.senha):
            raise LoginInvalido()

        return self._gerar_token({"sub": str(empresa.id), "role": "empresa"})