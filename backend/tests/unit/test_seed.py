import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import verificar_senha
from app.models import Armario, PapelUsuario, StatusArmario, Usuario
from app.seed import ARMARIOS_INICIAIS, popular, validar_senha_admin


def test_seed_cria_admin_e_armarios(db_session: Session) -> None:
    resultado = popular(db_session, "Admin@Locky.com", "admin123")

    assert resultado.admin_criado is True
    assert resultado.armarios_criados == len(ARMARIOS_INICIAIS) == 12

    admin = db_session.scalars(select(Usuario)).one()
    assert admin.email == "admin@locky.com"
    assert admin.papel == PapelUsuario.ADMIN
    assert verificar_senha("admin123", admin.senha_hash)

    status = set(db_session.scalars(select(Armario.status)).all())
    assert status == {StatusArmario.DISPONIVEL}


def test_seed_e_idempotente(db_session: Session) -> None:
    popular(db_session, "admin@locky.com", "admin123")
    resultado = popular(db_session, "admin@locky.com", "outra-senha")

    assert resultado.admin_criado is False
    assert resultado.armarios_criados == 0
    assert db_session.scalar(select(func.count()).select_from(Usuario)) == 1
    assert db_session.scalar(select(func.count()).select_from(Armario)) == 12


def test_seed_completa_armarios_faltantes(db_session: Session) -> None:
    db_session.add(Armario(numero="01", tamanho=ARMARIOS_INICIAIS[0][1]))
    db_session.commit()

    resultado = popular(db_session, "admin@locky.com", "admin123")

    assert resultado.armarios_criados == 11


def test_senha_padrao_aceita_fora_de_producao() -> None:
    validar_senha_admin("dev", "admin123")


def test_producao_recusa_senha_padrao() -> None:
    with pytest.raises(ValueError, match="senha padrão"):
        validar_senha_admin("prod", "admin123")


def test_producao_recusa_senha_curta() -> None:
    with pytest.raises(ValueError, match="pelo menos 10"):
        validar_senha_admin("prod", "curta123")


def test_producao_aceita_senha_forte() -> None:
    validar_senha_admin("prod", "uma-senha-bem-longa")
