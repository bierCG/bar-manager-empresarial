from sqlalchemy.orm import Session

from app.core.database.models import Usuario

class UsuarioRepository():
    def __init__(self, session: Session):
        self.session = session

    def create(self, usuario: Usuario) -> Usuario:
        self.session.add(usuario)
        self.session.commit()
        self.session.refresh(usuario)
        return usuario

    def update(self, usuario: Usuario) -> Usuario:
        self.session.commit()
        self.session.refresh(usuario)
        return usuario

    def get_by_id(self, usuario_id: int, empresa_id: int) -> Usuario | None:
        return (
            self.session.query(Usuario)
            .where(
                Usuario.id == usuario_id,
                Usuario.empresa_id == empresa_id
            ).first()
        )

    def get_by_username(self, username: str, empresa_id: int) -> Usuario | None:
         return (
             self.session.query(Usuario)
             .where(
                Usuario.usuario == username,
                Usuario.empresa_id == empresa_id
            ).first()
         )

    def get_usuarios_empresa(self, empresa_id: int) -> list[Usuario] | list:
        return (
            self.session.query(Usuario)
            .where(Usuario.empresa_id == empresa_id)
            .all()
        )