from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import expirar_vencidas, get_current_user
from app.core.db import get_session
from app.core.exceptions import (
    ArmarioIndisponivelError,
    ArmarioNaoEncontradoError,
    ReservaDeOutroUsuarioError,
    ReservaNaoEncontradaError,
    ReservaNaoPodeSerCanceladaError,
    UsuarioComReservaAtivaError,
)
from app.models import Usuario
from app.schemas.reservation import (
    CreateReservationRequest,
    ReservationListResponse,
    ReservationResponse,
    ReservationStatusAPI,
)
from app.services import reservation_service

router = APIRouter(
    prefix="/reservations",
    tags=["reservations"],
    dependencies=[Depends(expirar_vencidas)],
)


@router.post(
    "", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED
)
def criar_reserva(
    dados: CreateReservationRequest,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_current_user)],
) -> ReservationResponse:
    try:
        reserva, armario = reservation_service.criar_reserva(
            session, usuario.id, dados.locker_id, dados.date, dados.time
        )
    except UsuarioComReservaAtivaError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Usuário já possui uma reserva ativa.",
        ) from None
    except ArmarioNaoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Armário não encontrado.",
        ) from None
    except ArmarioIndisponivelError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Armário não está disponível.",
        ) from None

    return ReservationResponse.from_model(reserva, armario)


@router.get("/me", response_model=list[ReservationResponse])
def minhas_reservas(
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_current_user)],
    status: Annotated[ReservationStatusAPI | None, Query()] = None,
) -> list[ReservationResponse]:
    resultados = reservation_service.listar_minhas(session, usuario.id, status)
    return [ReservationResponse.from_model(r, a) for r, a in resultados]


@router.get("/me/history", response_model=ReservationListResponse)
def historico_reservas(
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_current_user)],
    search: Annotated[str | None, Query()] = None,
    status: Annotated[ReservationStatusAPI | None, Query()] = None,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ReservationListResponse:
    itens, total = reservation_service.listar_historico(
        session, usuario.id, search, status, start_date, end_date, limit, offset
    )
    return ReservationListResponse(
        items=[ReservationResponse.from_model(r, a) for r, a in itens],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch("/{reservation_id}/cancel", response_model=ReservationResponse)
def cancelar_reserva(
    reservation_id: int,
    session: Annotated[Session, Depends(get_session)],
    usuario: Annotated[Usuario, Depends(get_current_user)],
) -> ReservationResponse:
    try:
        reserva, armario = reservation_service.cancelar_reserva(
            session, usuario.id, reservation_id
        )
    except ReservaNaoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva não encontrada.",
        ) from None
    except ReservaDeOutroUsuarioError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reserva pertence a outro usuário.",
        ) from None
    except ReservaNaoPodeSerCanceladaError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reserva não pode ser cancelada.",
        ) from None

    return ReservationResponse.from_model(reserva, armario)
