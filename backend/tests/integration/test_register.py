from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import PapelUsuario, Usuario
from tests.conftest import SENHA_TESTE

NOVO_USUARIO = {"name": "Bruno", "email": "bruno@locky.com", "password": "segredo1"}


def test_register_cria_associado(client: TestClient, db_session: Session) -> None:
    resposta = client.post("/auth/register", json=NOVO_USUARIO)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["name"] == "Bruno"
    assert corpo["email"] == "bruno@locky.com"
    assert corpo["role"] == "associado"
    assert "password" not in corpo

    salvo = db_session.get(Usuario, corpo["id"])
    assert salvo is not None
    assert salvo.senha_hash != NOVO_USUARIO["password"]


def test_register_ignora_papel_enviado_pelo_cliente(client: TestClient) -> None:
    resposta = client.post("/auth/register", json={**NOVO_USUARIO, "role": "admin"})

    assert resposta.status_code == 201
    assert resposta.json()["role"] == PapelUsuario.ASSOCIADO


def test_register_permite_login_em_seguida(client: TestClient) -> None:
    client.post("/auth/register", json=NOVO_USUARIO)

    resposta = client.post(
        "/auth/login",
        json={"email": "BRUNO@locky.com", "password": NOVO_USUARIO["password"]},
    )

    assert resposta.status_code == 200
    assert resposta.json()["access_token"]


def test_register_normaliza_email(client: TestClient) -> None:
    resposta = client.post(
        "/auth/register", json={**NOVO_USUARIO, "email": "Bruno@Locky.COM"}
    )

    assert resposta.json()["email"] == "bruno@locky.com"


def test_register_email_duplicado(client: TestClient, usuario: Usuario) -> None:
    resposta = client.post(
        "/auth/register",
        json={"name": "Outra", "email": usuario.email.upper(), "password": "123456"},
    )

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Já existe uma conta com este e-mail."


def test_register_email_duplicado_em_corrida(client: TestClient) -> None:
    # Simula a outra requisição vencendo entre a checagem e o commit.
    with patch(
        "app.services.auth_service.usuario_repository.buscar_por_email",
        return_value=None,
    ):
        client.post("/auth/register", json=NOVO_USUARIO)
        with patch(
            "sqlalchemy.orm.Session.commit",
            side_effect=IntegrityError("insert", {}, Exception("duplicado")),
        ):
            resposta = client.post("/auth/register", json=NOVO_USUARIO)

    assert resposta.status_code == 409


def test_register_senha_curta(client: TestClient) -> None:
    resposta = client.post("/auth/register", json={**NOVO_USUARIO, "password": "123"})

    assert resposta.status_code == 422
    assert "password" in resposta.json()["detail"]


def test_register_senha_acima_do_limite_do_bcrypt(client: TestClient) -> None:
    resposta = client.post(
        "/auth/register", json={**NOVO_USUARIO, "password": "a" * 73}
    )

    assert resposta.status_code == 422


def test_register_nome_vazio(client: TestClient) -> None:
    resposta = client.post("/auth/register", json={**NOVO_USUARIO, "name": "A"})

    assert resposta.status_code == 422


def test_register_email_invalido(client: TestClient) -> None:
    resposta = client.post(
        "/auth/register", json={**NOVO_USUARIO, "email": "nao-e-email"}
    )

    assert resposta.status_code == 422


def test_login_continua_funcionando_para_usuario_existente(
    client: TestClient, usuario: Usuario
) -> None:
    resposta = client.post(
        "/auth/login", json={"email": usuario.email, "password": SENHA_TESTE}
    )

    assert resposta.status_code == 200
