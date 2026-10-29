from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registra os models em Base.metadata)
from app.core.db import Base, get_session
from app.core.security import hash_senha
from app.main import create_app
from app.models import Armario, PapelUsuario, StatusArmario, TamanhoArmario, Usuario

SENHA_TESTE = "senha123"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(db_session: Session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    return TestClient(app)


@pytest.fixture
def usuario(db_session: Session) -> Usuario:
    registro = Usuario(
        email="ana@locky.com",
        senha_hash=hash_senha(SENHA_TESTE),
        nome="Ana",
        papel=PapelUsuario.ASSOCIADO,
    )
    db_session.add(registro)
    db_session.commit()
    db_session.refresh(registro)
    return registro


@pytest.fixture
def auth_headers(client: TestClient, usuario: Usuario) -> dict[str, str]:
    resposta = client.post(
        "/auth/login", json={"email": usuario.email, "password": SENHA_TESTE}
    )
    token = resposta.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def armario_disponivel(db_session: Session) -> Armario:
    registro = Armario(
        numero="01", status=StatusArmario.DISPONIVEL, tamanho=TamanhoArmario.MEDIO
    )
    db_session.add(registro)
    db_session.commit()
    db_session.refresh(registro)
    return registro


@pytest.fixture
def admin(db_session: Session) -> Usuario:
    registro = Usuario(
        email="admin@locky.com",
        senha_hash=hash_senha(SENHA_TESTE),
        nome="Admin",
        papel=PapelUsuario.ADMIN,
    )
    db_session.add(registro)
    db_session.commit()
    db_session.refresh(registro)
    return registro


@pytest.fixture
def admin_headers(client: TestClient, admin: Usuario) -> dict[str, str]:
    resposta = client.post(
        "/auth/login", json={"email": admin.email, "password": SENHA_TESTE}
    )
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}
