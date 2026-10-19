# ------------------------------------------------------------------------------------------
#
# ### Erros De Operação ###
#
# ------------------------------------------------------------------------------------------


class ErroOperacional(Exception):
    status_code = 500
    message = "Erro Operacional"

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


# ------------------------------------------------------------------------------------------
#
# ### Erros De Negócio ###
#
# ------------------------------------------------------------------------------------------


class ErroDeNegocio(Exception):
    status_code = 400
    message = "Erro de negócio"

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class EventoDesconhecido(ErroDeNegocio):
    status_code = 400
    message = "Evento desconhecido"


class CancelamentoInvalido(ErroDeNegocio):
    status_code = 400
    message = "Pedido não pode ser cancelado"


class PedidoNaoPodeSerFinalizado(ErroDeNegocio):
    status_code = 499
    message = "Pedido não pode ser finalizado"

class PedidoNaoPodeSerEntregue(ErroDeNegocio):
    status_code = 499
    message = "Pedido aberto não pode ser entregue"

class PedidoNaoPodeSerEntregue(ErroDeNegocio):
    status_code = 400
    message = "Pedido não pode ser entregue"


class PedidoNaoEncontrado(ErroDeNegocio):
    status_code = 400
    message = "Pedido não encontrado"


class SemPermissao(ErroDeNegocio):
    status_code = 400
    message = "Você não tem permissão para esta ação"


class LoginInvalido(ErroDeNegocio):
    status_code = 401
    message = "Usuário ou senha inválidos"


class RoleDesconhecida(ErroDeNegocio):
    status_code = 400
    message = "Role desconhecida"


class CNPJDuplicado(ErroDeNegocio):
    status_code=409
    message="CNPJ Já possui cadastrado"

class EmpresaNaoEncontrada(ErroDeNegocio):
    status_code=404
    message="Empresa não encontrado"

class ProdutoNaoEncontrado(ErroDeNegocio):
    status_code=404
    message="Produto não encontrado"

class UsuarioDuplicado(ErroDeNegocio):
    status_code=409
    message="Usuário já possui cadastro"

class UsuarioNaoEncontrado(ErroDeNegocio):
    status_code=404
    message="Usuário não encontrado"