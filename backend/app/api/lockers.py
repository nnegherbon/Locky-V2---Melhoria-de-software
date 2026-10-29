from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import expirar_vencidas, get_current_user, require_admin
from app.core.db import get_session
from app.core.exceptions import (
    ArmarioComHistoricoError,
    ArmarioComReservaAtivaError,
    ArmarioNaoEncontradoError,
    NumeroArmarioDuplicadoError,
)
from app.schemas.locker import (
    CreateLockerRequest,
    LockerListResponse,
    LockerResponse,
    LockerSizeAPI,
    LockerStatsResponse,
    LockerStatusAPI,
    UpdateLockerRequest,
)
from app.services import locker_service

router = APIRouter(
    prefix="/lockers",
    tags=["lockers"],
    dependencies=[Depends(get_current_user), Depends(expirar_vencidas)],
)


def _nao_encontrado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Armário não encontrado."
    )


def _numero_duplicado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Já existe um armário com este número.",
    )


def _com_reserva_ativa() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Armário possui uma reserva ativa. Aguarde o fim ou o cancelamento.",
    )


def _com_historico() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            "Armário possui histórico de reservas e não pode ser excluído. "
            "Coloque-o em manutenção para retirá-lo de uso."
        ),
    )


@router.get("", response_model=LockerListResponse)
def listar_lockers(
    session: Annotated[Session, Depends(get_session)],
    status: Annotated[LockerStatusAPI | None, Query()] = None,
    size: Annotated[LockerSizeAPI | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LockerListResponse:
    armarios, total = locker_service.listar_armarios(
        session, status, size, limit, offset
    )
    return LockerListResponse(
        items=[LockerResponse.from_model(armario) for armario in armarios],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=LockerStatsResponse)
def stats_lockers(
    session: Annotated[Session, Depends(get_session)],
) -> LockerStatsResponse:
    return locker_service.obter_stats(session)


@router.post(
    "",
    response_model=LockerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def criar_locker(
    dados: CreateLockerRequest,
    session: Annotated[Session, Depends(get_session)],
) -> LockerResponse:
    try:
        armario = locker_service.criar_armario(session, dados)
    except NumeroArmarioDuplicadoError:
        raise _numero_duplicado() from None
    return LockerResponse.from_model(armario)


@router.patch(
    "/{locker_id}",
    response_model=LockerResponse,
    dependencies=[Depends(require_admin)],
)
def atualizar_locker(
    locker_id: int,
    dados: UpdateLockerRequest,
    session: Annotated[Session, Depends(get_session)],
) -> LockerResponse:
    try:
        armario = locker_service.atualizar_armario(session, locker_id, dados)
    except ArmarioNaoEncontradoError:
        raise _nao_encontrado() from None
    except NumeroArmarioDuplicadoError:
        raise _numero_duplicado() from None
    except ArmarioComReservaAtivaError:
        raise _com_reserva_ativa() from None
    return LockerResponse.from_model(armario)


@router.delete(
    "/{locker_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def excluir_locker(
    locker_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    try:
        locker_service.excluir_armario(session, locker_id)
    except ArmarioNaoEncontradoError:
        raise _nao_encontrado() from None
    except ArmarioComReservaAtivaError:
        raise _com_reserva_ativa() from None
    except ArmarioComHistoricoError:
        raise _com_historico() from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
