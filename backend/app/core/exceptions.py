class CredenciaisInvalidasError(Exception):
    """Credenciais de login inválidas ou token não autenticável."""


class EmailJaCadastradoError(Exception):
    """Já existe um usuário cadastrado com o e-mail informado."""


class ArmarioNaoEncontradoError(Exception):
    """Armário referenciado não existe."""


class ArmarioIndisponivelError(Exception):
    """Armário não está com status DISPONIVEL."""


class UsuarioComReservaAtivaError(Exception):
    """Usuário já possui uma reserva com status ATIVA."""


class ReservaNaoEncontradaError(Exception):
    """Reserva referenciada não existe."""


class ReservaDeOutroUsuarioError(Exception):
    """Reserva pertence a outro usuário."""


class ReservaNaoPodeSerCanceladaError(Exception):
    """Reserva não está com status ATIVA, não pode ser cancelada."""
