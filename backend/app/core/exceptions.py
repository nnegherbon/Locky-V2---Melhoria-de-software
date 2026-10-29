class CredenciaisInvalidasError(Exception):
    """Credenciais de login inválidas ou token não autenticável."""


class EmailJaCadastradoError(Exception):
    """Já existe um usuário cadastrado com o e-mail informado."""


class ArmarioNaoEncontradoError(Exception):
    """Armário referenciado não existe."""


class ArmarioIndisponivelError(Exception):
    """Armário não está com status DISPONIVEL."""


class NumeroArmarioDuplicadoError(Exception):
    """Já existe um armário com o número informado."""


class ArmarioComReservaAtivaError(Exception):
    """Armário possui reserva ATIVA e não pode ter o status alterado/ser excluído."""


class ArmarioComHistoricoError(Exception):
    """Armário já teve reservas; excluí-lo apagaria o histórico dos usuários."""


class UsuarioComReservaAtivaError(Exception):
    """Usuário já possui uma reserva com status ATIVA."""


class ReservaNaoEncontradaError(Exception):
    """Reserva referenciada não existe."""


class ReservaDeOutroUsuarioError(Exception):
    """Reserva pertence a outro usuário."""


class ReservaNaoPodeSerCanceladaError(Exception):
    """Reserva não está com status ATIVA, não pode ser cancelada."""
