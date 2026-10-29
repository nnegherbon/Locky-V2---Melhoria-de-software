from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings


def agora_local() -> datetime:
    """Agora no fuso da academia, sem tzinfo (mesmo formato das colunas data/hora).

    `datetime.now()` usaria o fuso do servidor: em UTC, uma reserva para daqui a
    30 minutos em São Paulo seria recusada como "no passado".
    """
    return datetime.now(ZoneInfo(settings.fuso_horario)).replace(tzinfo=None)
