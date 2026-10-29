"""Popula o banco com um administrador e armários iniciais.

Uso:  uv run python -m app.seed

É idempotente: pode ser executado várias vezes sem duplicar registros.
Credenciais do admin vêm de SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD (.env).
"""

import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_senha
from app.models import Armario, PapelUsuario, TamanhoArmario, Usuario
from app.repositories import usuario_repository

logger = logging.getLogger(__name__)

# 12 armários: 4 de cada tamanho, numerados 01..12.
ARMARIOS_INICIAIS: list[tuple[str, TamanhoArmario]] = [
    (f"{numero:02d}", tamanho)
    for numero, tamanho in enumerate(
        [TamanhoArmario.PEQUENO] * 4
        + [TamanhoArmario.MEDIO] * 4
        + [TamanhoArmario.GRANDE] * 4,
        start=1,
    )
]


@dataclass(frozen=True)
class ResultadoSeed:
    admin_criado: bool
    armarios_criados: int


def popular(session: Session, email_admin: str, senha_admin: str) -> ResultadoSeed:
    admin_criado = False
    email = email_admin.strip().lower()
    if usuario_repository.buscar_por_email(session, email) is None:
        session.add(
            Usuario(
                nome="Administrador",
                email=email,
                senha_hash=hash_senha(senha_admin),
                papel=PapelUsuario.ADMIN,
            )
        )
        admin_criado = True

    existentes = set(session.scalars(select(Armario.numero)).all())
    novos = [
        Armario(numero=numero, tamanho=tamanho)
        for numero, tamanho in ARMARIOS_INICIAIS
        if numero not in existentes
    ]
    session.add_all(novos)
    session.commit()
    return ResultadoSeed(admin_criado=admin_criado, armarios_criados=len(novos))


def main() -> None:  # pragma: no cover - ponto de entrada de linha de comando
    from app.core.db import SessionLocal
    from app.core.logging_config import configurar_logging

    configurar_logging()
    with SessionLocal() as session:
        resultado = popular(
            session, settings.seed_admin_email, settings.seed_admin_password
        )
    logger.info(
        "Seed concluído: admin %s, %d armário(s) criado(s).",
        "criado" if resultado.admin_criado else "já existia",
        resultado.armarios_criados,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
