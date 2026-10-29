from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Armario, StatusArmario, TamanhoArmario


def listar(
    session: Session,
    status: StatusArmario | None,
    tamanho: TamanhoArmario | None,
    limit: int,
    offset: int,
) -> tuple[list[Armario], int]:
    condicoes = []
    if status is not None:
        condicoes.append(Armario.status == status)
    if tamanho is not None:
        condicoes.append(Armario.tamanho == tamanho)

    consulta = select(Armario)
    if condicoes:
        consulta = consulta.where(*condicoes)

    total = session.scalar(select(func.count()).select_from(consulta.subquery()))

    itens = session.scalars(
        consulta.order_by(Armario.numero).offset(offset).limit(limit)
    ).all()

    return list(itens), total or 0


def contar_por_status(session: Session) -> dict[StatusArmario, int]:
    linhas = session.execute(
        select(Armario.status, func.count()).group_by(Armario.status)
    ).tuples()
    return dict(linhas.all())


def buscar_para_atualizar(session: Session, armario_id: int) -> Armario | None:
    return session.execute(
        select(Armario)
        .where(Armario.id == armario_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()


def buscar_por_numero(session: Session, numero: str) -> Armario | None:
    return session.scalars(select(Armario).where(Armario.numero == numero)).first()
