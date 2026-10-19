from sqlalchemy.orm import Session

from app.core.database.models import Produto
from app.core.exceptions.errors import ProdutoNaoEncontrado
from app.repositories.produtos import ProdutoRepository
from app.schemas.produto import CreateRequest, UpdateRequest


class ProdutoService:
    def __init__(self, session: Session):
        self.repo = ProdutoRepository(session)

    def cadastrar_produto(self, cadastro: CreateRequest, empresa_id: int) -> Produto:
        produto = Produto(**cadastro.model_dump(), empresa_id=empresa_id)
        return self.repo.create(produto)

    def atualizar_cadastro(self, dados: UpdateRequest, produto_id: int, empresa_id: int) -> Produto:
        produto = self.repo.get_produto(produto_id, empresa_id)

        if not produto:
            raise ProdutoNaoEncontrado

        campos = dados.model_dump(exclude_unset=True, exclude_none=True)
        for campo, valor in campos.items():
            setattr(produto, campo, valor)

        return self.repo.update(produto)

    def listar_produtos(self, empresa_id: int) -> list[Produto]:
        return self.repo.get_all(empresa_id)