from sqlalchemy.orm import Session

from app.core.database.models import Empresa

class EmpresaRepository():
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, empresa_id: int) -> Empresa | None:
        return self.session.query(Empresa).where(Empresa.id == empresa_id).first()

    def get_by_username(self, usuario: str) -> Empresa | None:
        return self.session.query(Empresa).where(Empresa.usuario == usuario).first()

    def get_by_cnpj(self, cnpj: str) -> Empresa | None:
        return self.session.query(Empresa).where(Empresa.cnpj == cnpj).first()

    def get_all(self) -> list[Empresa]:
        return self.session.query(Empresa).all()

    def create(self, empresa: Empresa) -> Empresa:
        self.session.add(empresa)
        self.session.commit()
        self.session.refresh(empresa)
        return empresa

    def update(self, empresa: Empresa) -> Empresa:
        self.session.commit()
        self.session.refresh(empresa)
        return empresa