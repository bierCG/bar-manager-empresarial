from sqladmin import ModelView

from app.core.database.models import Empresa, Usuario, Produto, Pedido

class EmpresaAdmin(ModelView, model=Empresa):
    column_list = [Empresa.id, Empresa.nome, Empresa.cnpj]
    column_searchable_list = [Empresa.nome]
    column_sortable_list = [Empresa.id, Empresa.nome]

class UsuarioAdmin(ModelView, model=Usuario):
    column_list = [Usuario.id, Usuario.nome, Usuario.role]
    column_searchable_list = [Usuario.role]
    column_sortable_list = [Usuario.role]

class ProdutoAdmin(ModelView, model=Produto):
    column_list = [Produto.id, Produto.nome, Produto.valor]
    column_searchable_list = [Produto.nome]
    column_sortable_list = [Produto.nome, Produto.valor]

class PedidoAdmin(ModelView, model=Pedido):
    column_list = [Pedido.id, Pedido.usuario_id, Pedido.produto, Produto.empresa_id]
    column_searchable_list = [Pedido.usuario_id, Produto.empresa_id]