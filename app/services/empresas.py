from sqlalchemy.orm import Session

from app.core.database.models import Empresa
from app.core.exceptions.errors import CNPJDuplicado, EmpresaNaoEncontrada
from app.core.security.password import hash_senha
from app.repositories.empresas import EmpresaRepository
from app.schemas.empresa import CreateRequestEmpresa, UpdateRequestEmpresa

class EmpresaService():
    def __init__(self, session: Session):
        self.repo = EmpresaRepository(session)

    def cadastrar(self, cadastro: CreateRequestEmpresa) -> Empresa:
        if self.repo.get_by_cnpj(cadastro.cnpj):
            raise CNPJDuplicado()

        empresa = Empresa(
            **cadastro.model_dump(exclude={"senha"}),
            senha=hash_senha(cadastro.senha)
        )
        return self.repo.create(empresa)

    def atualizar_cadastro(self, dados: UpdateRequestEmpresa, empresa_id: int) -> Empresa:
        empresa = self.repo.get_by_id(empresa_id)
        if not empresa:
            raise EmpresaNaoEncontrada()

        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(empresa, campo, valor)
        
        return self.repo.update(empresa)

    def listar_empresas(self) -> list[Empresa]:
        return self.repo.get_all()