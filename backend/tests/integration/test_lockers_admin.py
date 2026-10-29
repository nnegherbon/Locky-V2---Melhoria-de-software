from datetime import date, time
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Armario,
    Reserva,
    StatusArmario,
    StatusReserva,
    TamanhoArmario,
    Usuario,
)

NOVO = {"number": "20", "size": "large"}


def _reservar(
    db_session: Session,
    usuario: Usuario,
    armario: Armario,
    status: StatusReserva = StatusReserva.ATIVA,
) -> None:
    db_session.add(
        Reserva(
            usuario_id=usuario.id,
            armario_id=armario.id,
            data=date(2030, 1, 1),
            hora=time(10, 0),
            status=status,
        )
    )
    if status == StatusReserva.ATIVA:
        armario.status = StatusArmario.RESERVADO
    db_session.commit()


# ---------- Autorização ----------


def test_associado_nao_pode_criar(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    resposta = client.post("/lockers", json=NOVO, headers=auth_headers)

    assert resposta.status_code == 403
    assert resposta.json()["detail"] == "Acesso restrito a administradores."


def test_associado_nao_pode_editar_nem_excluir(
    client: TestClient, auth_headers: dict[str, str], armario_disponivel: Armario
) -> None:
    url = f"/lockers/{armario_disponivel.id}"

    assert client.patch(url, json={}, headers=auth_headers).status_code == 403
    assert client.delete(url, headers=auth_headers).status_code == 403


def test_sem_token_retorna_401(client: TestClient) -> None:
    assert client.post("/lockers", json=NOVO).status_code == 401


# ---------- Criar ----------


def test_admin_cria_armario(
    client: TestClient, admin_headers: dict[str, str], db_session: Session
) -> None:
    resposta = client.post(
        "/lockers", json={"number": "  20 ", "size": "large"}, headers=admin_headers
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["number"] == "20"
    assert corpo["size"] == "large"
    assert corpo["status"] == "available"

    salvo = db_session.get(Armario, corpo["id"])
    assert salvo is not None
    assert salvo.tamanho == TamanhoArmario.GRANDE


def test_admin_cria_armario_em_manutencao(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    resposta = client.post(
        "/lockers", json={**NOVO, "status": "maintenance"}, headers=admin_headers
    )

    assert resposta.json()["status"] == "maintenance"


def test_criar_com_status_derivado_de_reserva_e_rejeitado(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    resposta = client.post(
        "/lockers", json={**NOVO, "status": "reserved"}, headers=admin_headers
    )

    assert resposta.status_code == 422


def test_criar_numero_duplicado(
    client: TestClient, admin_headers: dict[str, str], armario_disponivel: Armario
) -> None:
    resposta = client.post(
        "/lockers",
        json={"number": armario_disponivel.numero, "size": "small"},
        headers=admin_headers,
    )

    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Já existe um armário com este número."


def test_criar_numero_duplicado_em_corrida(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    with patch(
        "sqlalchemy.orm.Session.commit",
        side_effect=IntegrityError("insert", {}, Exception("duplicado")),
    ):
        resposta = client.post("/lockers", json=NOVO, headers=admin_headers)

    assert resposta.status_code == 409


def test_criar_numero_vazio_ou_longo(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    vazio = client.post(
        "/lockers", json={"number": "   ", "size": "small"}, headers=admin_headers
    )
    longo = client.post(
        "/lockers", json={"number": "1" * 11, "size": "small"}, headers=admin_headers
    )

    assert vazio.status_code == 422
    assert longo.status_code == 422


# ---------- Editar ----------


def test_admin_edita_numero_e_tamanho(
    client: TestClient, admin_headers: dict[str, str], armario_disponivel: Armario
) -> None:
    resposta = client.patch(
        f"/lockers/{armario_disponivel.id}",
        json={"number": "99", "size": "small"},
        headers=admin_headers,
    )

    assert resposta.status_code == 200
    assert resposta.json()["number"] == "99"
    assert resposta.json()["size"] == "small"
    assert resposta.json()["status"] == "available"


def test_admin_coloca_e_retira_manutencao(
    client: TestClient, admin_headers: dict[str, str], armario_disponivel: Armario
) -> None:
    url = f"/lockers/{armario_disponivel.id}"

    em_manutencao = client.patch(
        url, json={"status": "maintenance"}, headers=admin_headers
    )
    liberado = client.patch(url, json={"status": "available"}, headers=admin_headers)

    assert em_manutencao.json()["status"] == "maintenance"
    assert liberado.json()["status"] == "available"


def test_armario_em_manutencao_nao_pode_ser_reservado(
    client: TestClient,
    admin_headers: dict[str, str],
    auth_headers: dict[str, str],
    armario_disponivel: Armario,
) -> None:
    client.patch(
        f"/lockers/{armario_disponivel.id}",
        json={"status": "maintenance"},
        headers=admin_headers,
    )

    resposta = client.post(
        "/reservations",
        json={
            "locker_id": armario_disponivel.id,
            "date": "2030-01-01",
            "time": "10:00",
        },
        headers=auth_headers,
    )

    assert resposta.status_code == 409


def test_editar_mantendo_o_proprio_numero(
    client: TestClient, admin_headers: dict[str, str], armario_disponivel: Armario
) -> None:
    resposta = client.patch(
        f"/lockers/{armario_disponivel.id}",
        json={"number": armario_disponivel.numero, "status": "available"},
        headers=admin_headers,
    )

    assert resposta.status_code == 200


def test_editar_para_numero_de_outro_armario(
    client: TestClient,
    admin_headers: dict[str, str],
    db_session: Session,
    armario_disponivel: Armario,
) -> None:
    db_session.add(Armario(numero="02", tamanho=TamanhoArmario.PEQUENO))
    db_session.commit()

    resposta = client.patch(
        f"/lockers/{armario_disponivel.id}",
        json={"number": "02"},
        headers=admin_headers,
    )

    assert resposta.status_code == 409


def test_editar_status_de_armario_reservado_e_bloqueado(
    client: TestClient,
    admin_headers: dict[str, str],
    db_session: Session,
    usuario: Usuario,
    armario_disponivel: Armario,
) -> None:
    _reservar(db_session, usuario, armario_disponivel)

    resposta = client.patch(
        f"/lockers/{armario_disponivel.id}",
        json={"status": "maintenance"},
        headers=admin_headers,
    )

    assert resposta.status_code == 409
    db_session.refresh(armario_disponivel)
    assert armario_disponivel.status == StatusArmario.RESERVADO


def test_editar_numero_de_armario_reservado_e_permitido(
    client: TestClient,
    admin_headers: dict[str, str],
    db_session: Session,
    usuario: Usuario,
    armario_disponivel: Armario,
) -> None:
    _reservar(db_session, usuario, armario_disponivel)

    resposta = client.patch(
        f"/lockers/{armario_disponivel.id}",
        json={"number": "01-A"},
        headers=admin_headers,
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "reserved"


def test_editar_inexistente(client: TestClient, admin_headers: dict[str, str]) -> None:
    resposta = client.patch("/lockers/999", json={}, headers=admin_headers)

    assert resposta.status_code == 404


def test_editar_numero_vazio(
    client: TestClient, admin_headers: dict[str, str], armario_disponivel: Armario
) -> None:
    resposta = client.patch(
        f"/lockers/{armario_disponivel.id}",
        json={"number": " "},
        headers=admin_headers,
    )

    assert resposta.status_code == 422


# ---------- Excluir ----------


def test_admin_exclui_armario_sem_reservas(
    client: TestClient,
    admin_headers: dict[str, str],
    db_session: Session,
    armario_disponivel: Armario,
) -> None:
    armario_id = armario_disponivel.id

    resposta = client.delete(f"/lockers/{armario_id}", headers=admin_headers)

    assert resposta.status_code == 204
    db_session.expire_all()
    assert db_session.get(Armario, armario_id) is None


def test_excluir_armario_com_reserva_ativa(
    client: TestClient,
    admin_headers: dict[str, str],
    db_session: Session,
    usuario: Usuario,
    armario_disponivel: Armario,
) -> None:
    _reservar(db_session, usuario, armario_disponivel)

    resposta = client.delete(f"/lockers/{armario_disponivel.id}", headers=admin_headers)

    assert resposta.status_code == 409
    assert "reserva ativa" in resposta.json()["detail"]


def test_excluir_armario_com_historico(
    client: TestClient,
    admin_headers: dict[str, str],
    db_session: Session,
    usuario: Usuario,
    armario_disponivel: Armario,
) -> None:
    _reservar(db_session, usuario, armario_disponivel, StatusReserva.CANCELADA)

    resposta = client.delete(f"/lockers/{armario_disponivel.id}", headers=admin_headers)

    assert resposta.status_code == 409
    assert "manutenção" in resposta.json()["detail"]


def test_excluir_inexistente(client: TestClient, admin_headers: dict[str, str]) -> None:
    assert client.delete("/lockers/999", headers=admin_headers).status_code == 404
