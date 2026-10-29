from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.lockers import router as lockers_router
from app.api.reservations import router as reservations_router
from app.core.config import settings
from app.core.errors import registrar_exception_handlers
from app.core.logging_config import configurar_logging
from app.core.scheduler import iniciar_scheduler, parar_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Em serverless (Vercel) não há processo contínuo: a expiração acontece sob
    # demanda, nas próprias requisições (ver api/deps.py::expirar_vencidas).
    rodar = settings.executar_scheduler
    if rodar:
        iniciar_scheduler()
    yield
    if rodar:
        parar_scheduler()


def create_app() -> FastAPI:
    configurar_logging()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    registrar_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(lockers_router)
    app.include_router(reservations_router)
    return app


app = create_app()
