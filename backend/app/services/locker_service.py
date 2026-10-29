from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ArmarioComHistoricoError,
    ArmarioComReservaAtivaError,
    ArmarioNaoEncontradoError,
    NumeroArmarioDuplicadoError,
)
from app.models import Armario, StatusArmario
from app.repositories import armario_repository, reserva_repository
from app.schemas.locker import (
    STATUS_ADMIN_PARA_DOMINIO,
    STATUS_API_PARA_DOMINIO,
    TAMANHO_API_PARA_DOMINIO,
    CreateLockerRequest,
    LockerSizeAPI,
    LockerStatsResponse,
    LockerStatusAPI,
    UpdateLockerRequest,
)


def listar_armarios(
    session: Session,
    status: LockerStatusAPI | None,
    size: LockerSizeAPI | None,
    limit: int,
    offset: int,
) -> tuple[list[Armario], int]:
    status_dominio = STATUS_API_PARA_DOMINIO[status] if status is not None else None
    tamanho_dominio = TAMANHO_API_PARA_DOMINIO[size] if size is not None else None
    return armario_repository.listar(
        session, status_dominio, tamanho_dominio, limit, offset
    )


def obter_stats(session: Session) -> LockerStatsResponse:
    contagem = armario_repository.contar_por_status(session)
    return LockerStatsResponse(
        total=sum(contagem.values()),
        available=contagem.get(StatusArmario.DISPONIVEL, 0),
        reserved=contagem.get(StatusArmario.RESERVADO, 0),
        occupied=contagem.get(StatusArmario.OCUPADO, 0),
        maintenance=contagem.get(StatusArmario.MANUTENCAO, 0),
    )


def _garantir_numero_livre(
    session: Session, numero: str, ignorar_id: int | None = None
) -> None:
    existente = armario_repository.buscar_por_numero(session, numero)
    if existente is not None and existente.id != ignorar_id:
        raise NumeroArmarioDuplicadoError


def _salvar(session: Session, armario: Armario) -> Armario:
    try:
        session.commit()
    except IntegrityError as exc:
        # Corrida entre dois cadastros com o mesmo número: o índice único decide.
        session.rollback()
        raise NumeroArmarioDuplicadoError from exc
    session.refresh(armario)
    return armario


def criar_armario(session: Session, dados: CreateLockerRequest) -> Armario:
    _garantir_numero_livre(session, dados.number)
    armario = Armario(
        numero=dados.number,
        tamanho=TAMANHO_API_PARA_DOMINIO[dados.size],
        status=STATUS_ADMIN_PARA_DOMINIO[dados.status],
    )
    session.add(armario)
    return _salvar(session, armario)


def atualizar_armario(
    session: Session, armario_id: int, dados: UpdateLockerRequest
) -> Armario:
    armario = armario_repository.buscar_para_atualizar(session, armario_id)
    if armario is None:
        raise ArmarioNaoEncontradoError

    if dados.number is not None and dados.number != armario.numero:
        _garantir_numero_livre(session, dados.number, ignorar_id=armario.id)
        armario.numero = dados.number

    if dados.size is not None:
        armario.tamanho = TAMANHO_API_PARA_DOMINIO[dados.size]

    if dados.status is not None:
        novo_status = STATUS_ADMIN_PARA_DOMINIO[dados.status]
        if novo_status != armario.status:
            # Mexer no status de um armário reservado deixaria a reserva ativa
            # apontando para um armário "disponível" ou "em manutenção".
            if reserva_repository.armario_tem_reserva_ativa(session, armario.id):
                session.rollback()
                raise ArmarioComReservaAtivaError
            armario.status = novo_status

    return _salvar(session, armario)


def excluir_armario(session: Session, armario_id: int) -> None:
    armario = armario_repository.buscar_para_atualizar(session, armario_id)
    if armario is None:
        raise ArmarioNaoEncontradoError
    if reserva_repository.armario_tem_reserva_ativa(session, armario.id):
        session.rollback()
        raise ArmarioComReservaAtivaError
    if reserva_repository.armario_tem_reservas(session, armario.id):
        # Exclusão física quebraria a FK e apagaria o histórico dos associados.
        session.rollback()
        raise ArmarioComHistoricoError

    session.delete(armario)
    session.commit()
