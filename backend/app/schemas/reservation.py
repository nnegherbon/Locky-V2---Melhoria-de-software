from datetime import date as Date
from datetime import datetime
from datetime import time as Time
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, model_validator

from app.core.clock import agora_local
from app.models import Armario, Reserva, StatusReserva
from app.schemas.locker import TAMANHO_DOMINIO_PARA_API, LockerSizeAPI


class ReservationStatusAPI(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


STATUS_RESERVA_PARA_API = {
    StatusReserva.ATIVA: ReservationStatusAPI.ACTIVE,
    StatusReserva.CONCLUIDA: ReservationStatusAPI.COMPLETED,
    StatusReserva.CANCELADA: ReservationStatusAPI.CANCELLED,
}
STATUS_API_PARA_RESERVA = {v: k for k, v in STATUS_RESERVA_PARA_API.items()}


class CreateReservationRequest(BaseModel):
    locker_id: int
    date: Date
    time: Time

    @model_validator(mode="after")
    def data_hora_nao_pode_estar_no_passado(self) -> Self:
        momento_reserva = datetime.combine(self.date, self.time)
        if momento_reserva < agora_local():
            raise ValueError("A data e hora da reserva não podem estar no passado.")
        return self


class ReservationResponse(BaseModel):
    id: int
    locker_id: int
    locker_number: str
    locker_size: LockerSizeAPI
    date: Date
    time: Time
    status: ReservationStatusAPI

    @classmethod
    def from_model(cls, reserva: Reserva, armario: Armario) -> "ReservationResponse":
        return cls(
            id=reserva.id,
            locker_id=armario.id,
            locker_number=armario.numero,
            locker_size=TAMANHO_DOMINIO_PARA_API[armario.tamanho],
            date=reserva.data,
            time=reserva.hora,
            status=STATUS_RESERVA_PARA_API[reserva.status],
        )


class ReservationListResponse(BaseModel):
    items: list[ReservationResponse]
    total: int
    limit: int
    offset: int
