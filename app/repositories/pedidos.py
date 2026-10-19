from sqlalchemy import update
from sqlalchemy.orm import Session
from app.core.database.models import Pedido

class PedidoRepository():
    def __init__(self, session: Session):
        self.session = session


    def get_pedido(self, pedido_id: int, empresa_id: int):
        return (
            self.session.query(Pedido)
                .filter(Pedido.id == pedido_id, Pedido.empresa_id == empresa_id)
                .first()
        )


    def get_ultimos_pedidos(self, empresa_id: int, inicio, fim):
        return (
            self.session.query(Pedido)
                .filter(
                    Pedido.criado_em.between(inicio, fim),
                    Pedido.empresa_id == empresa_id
                )
                .all()
        )


    def get_bartender_ultimos_pedidos(self, usuario_id: int, empresa_id: int, inicio, fim):
        return (
            self.session.query(Pedido)
                .filter(
                    Pedido.usuario_id == usuario_id,
                    Pedido.empresa_id == empresa_id,
                    Pedido.criado_em.between(inicio, fim)
                )
                .all()
        )


    def create(self, pedido: Pedido) -> Pedido:
        self.session.add(pedido)
        self.session.commit()
        self.session.refresh(pedido)
        return pedido


    def update_status_pedido(self, pedido: Pedido) -> Pedido:
        self.session.commit()
        self.session.refresh(pedido)
        return pedido