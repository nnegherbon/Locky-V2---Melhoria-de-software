from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Armario, Reserva, StatusReserva


def existe_reserva_ativa(session: Session, usuario_id: int) -> bool:
    reserva = session.scalars(
        select(Reserva).where(
            Reserva.usuario_id == usuario_id,
            Reserva.status == StatusReserva.ATIVA,
        )
    ).first()
    return reserva is not None


def armario_tem_reserva_ativa(session: Session, armario_id: int) -> bool:
    return (
        session.scalars(
            select(Reserva.id).where(
                Reserva.armario_id == armario_id,
                Reserva.status == StatusReserva.ATIVA,
            )
        ).first()
        is not None
    )


def armario_tem_reservas(session: Session, armario_id: int) -> bool:
    return (
        session.scalars(
            select(Reserva.id).where(Reserva.armario_id == armario_id)
        ).first()
        is not None
    )


def buscar_para_atualizar(session: Session, reserva_id: int) -> Reserva | None:
    # populate_existing: se a reserva já estava carregada na sessão, recarrega os
    # valores do banco depois de obter o lock (outra transação pode tê-la mudado).
    return session.execute(
        select(Reserva)
        .where(Reserva.id == reserva_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()


def listar_ativas(session: Session) -> list[Reserva]:
    """Leitura sem lock: usada para achar candidatas a expirar."""
    return list(
        session.scalars(
            select(Reserva).where(Reserva.status == StatusReserva.ATIVA)
        ).all()
    )


def listar_por_usuario(
    session: Session, usuario_id: int, status: StatusReserva | None
) -> list[tuple[Reserva, Armario]]:
    condicoes = [Reserva.usuario_id == usuario_id]
    if status is not None:
        condicoes.append(Reserva.status == status)

    linhas = session.execute(
        select(Reserva, Armario)
        .join(Armario, Reserva.armario_id == Armario.id)
        .where(*condicoes)
        .order_by(Reserva.data.desc(), Reserva.hora.desc())
    ).all()
    return [(reserva, armario) for reserva, armario in linhas]


def listar_historico(
    session: Session,
    usuario_id: int,
    search: str | None,
    status: StatusReserva | None,
    data_inicial: date | None,
    data_final: date | None,
    limit: int,
    offset: int,
) -> tuple[list[tuple[Reserva, Armario]], int]:
    condicoes = [
        Reserva.usuario_id == usuario_id,
        Reserva.status != StatusReserva.ATIVA,
    ]
    if search:
        condicoes.append(Armario.numero.ilike(f"%{search}%"))
    if status is not None:
        condicoes.append(Reserva.status == status)
    if data_inicial is not None:
        condicoes.append(Reserva.data >= data_inicial)
    if data_final is not None:
        condicoes.append(Reserva.data <= data_final)

    consulta = (
        select(Reserva, Armario)
        .join(Armario, Reserva.armario_id == Armario.id)
        .where(*condicoes)
    )

    total = session.scalar(select(func.count()).select_from(consulta.subquery()))

    linhas = session.execute(
        consulta.order_by(Reserva.data.desc(), Reserva.hora.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return [(reserva, armario) for reserva, armario in linhas], total or 0
