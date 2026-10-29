from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

_opcoes_engine: dict[str, Any] = {"pool_pre_ping": True}
if settings.serverless:
    # Cada invocação serverless pode rodar em uma instância nova: manter um pool
    # deixaria conexões órfãs no banco. Use a URL "pooled" do provedor.
    _opcoes_engine["poolclass"] = NullPool

engine = create_engine(settings.database_url, **_opcoes_engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
