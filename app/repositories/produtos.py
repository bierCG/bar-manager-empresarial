from sqlalchemy.orm import Session

from app.core.database.models import Produto

class ProdutoRepository():
    def __init__(self, session: Session):
        self.session = session

    def get_produto(self, produto_id: int, empresa_id: int) -> Produto | None:
        return (
            self.session.query(Produto)
            .where(Produto.id == produto_id, Produto.empresa_id == empresa_id)
            .first()
        )

    def get_all(self, empresa_id: int) -> list[Produto]:
        return (
            self.session.query(Produto)
            .where(Produto.empresa_id == empresa_id)
            .all()
        )

    def create(self, produto: Produto):
        self.session.add(produto)
        self.session.commit()
        self.session.refresh(produto)
        return produto

    def update(self, produto: Produto) -> Produto:
        self.session.commit()
        self.session.refresh(produto)
        return produto