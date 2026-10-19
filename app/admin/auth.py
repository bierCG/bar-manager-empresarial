from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.database.connection import SessionLocal

from app.core.security.auth import create_token, validate_token
from app.core.security.password import validar_senha
from app.repositories.empresas import EmpresaRepository


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        usuario, password = form["username"], form["password"]

        with SessionLocal() as session:
            user = EmpresaRepository(session).get_by_username(usuario)

        if not user or not validar_senha(password, user.senha):
            return False
        # if not user.is_superuser:  # restrinja o acesso ao admin
            # return False

        payload = {
            "sub": str(user.id),
            "role": "empresa",
        }

        request.session.update({"token": create_token(payload)})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        try:
            validate_token(token)
        except Exception as e:
            return False
        return True