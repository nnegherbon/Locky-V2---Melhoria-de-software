from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from app.models import Armario, StatusArmario, TamanhoArmario


class LockerStatusAPI(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"


class LockerAdminStatusAPI(StrEnum):
    """Status que o administrador pode definir manualmente.

    `reserved` e `occupied` são consequência das reservas; permitir que o admin
    os definisse à mão deixaria o armário dessincronizado da tabela de reservas.
    """

    AVAILABLE = "available"
    MAINTENANCE = "maintenance"


class LockerSizeAPI(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


STATUS_DOMINIO_PARA_API = {
    StatusArmario.DISPONIVEL: LockerStatusAPI.AVAILABLE,
    StatusArmario.RESERVADO: LockerStatusAPI.RESERVED,
    StatusArmario.OCUPADO: LockerStatusAPI.OCCUPIED,
    StatusArmario.MANUTENCAO: LockerStatusAPI.MAINTENANCE,
}
STATUS_API_PARA_DOMINIO = {v: k for k, v in STATUS_DOMINIO_PARA_API.items()}

STATUS_ADMIN_PARA_DOMINIO = {
    LockerAdminStatusAPI.AVAILABLE: StatusArmario.DISPONIVEL,
    LockerAdminStatusAPI.MAINTENANCE: StatusArmario.MANUTENCAO,
}

TAMANHO_DOMINIO_PARA_API = {
    TamanhoArmario.PEQUENO: LockerSizeAPI.SMALL,
    TamanhoArmario.MEDIO: LockerSizeAPI.MEDIUM,
    TamanhoArmario.GRANDE: LockerSizeAPI.LARGE,
}
TAMANHO_API_PARA_DOMINIO = {v: k for k, v in TAMANHO_DOMINIO_PARA_API.items()}

# Mesmo limite da coluna `armarios.numero` (String(10)).
NUMERO_TAMANHO_MAXIMO = 10


class LockerResponse(BaseModel):
    id: int
    number: str
    status: LockerStatusAPI
    size: LockerSizeAPI

    @classmethod
    def from_model(cls, armario: Armario) -> "LockerResponse":
        return cls(
            id=armario.id,
            number=armario.numero,
            status=STATUS_DOMINIO_PARA_API[armario.status],
            size=TAMANHO_DOMINIO_PARA_API[armario.tamanho],
        )


class LockerListResponse(BaseModel):
    items: list[LockerResponse]
    total: int
    limit: int
    offset: int


class LockerStatsResponse(BaseModel):
    total: int
    available: int
    reserved: int
    occupied: int
    maintenance: int


def _normalizar_numero(valor: str) -> str:
    numero = valor.strip()
    if not numero:
        raise ValueError("O número do armário é obrigatório.")
    return numero


class CreateLockerRequest(BaseModel):
    number: str = Field(max_length=NUMERO_TAMANHO_MAXIMO)
    size: LockerSizeAPI
    status: LockerAdminStatusAPI = LockerAdminStatusAPI.AVAILABLE

    @field_validator("number")
    @classmethod
    def _numero(cls, valor: str) -> str:
        return _normalizar_numero(valor)


class UpdateLockerRequest(BaseModel):
    """Atualização parcial: só os campos enviados são alterados."""

    number: str | None = Field(default=None, max_length=NUMERO_TAMANHO_MAXIMO)
    size: LockerSizeAPI | None = None
    status: LockerAdminStatusAPI | None = None

    @field_validator("number")
    @classmethod
    def _numero(cls, valor: str | None) -> str | None:
        return None if valor is None else _normalizar_numero(valor)
