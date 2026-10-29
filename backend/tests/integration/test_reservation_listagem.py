from datetime import date, time

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import (
    Armario,
    Reserva,
    StatusArmario,
    StatusReserva,
    TamanhoArmario,
    Usuario,
)


def _seed_historico(db_session: Session, usuario_id: int) -> None:
    armarios = [
        Armario(
            numero="10", status=StatusArmario.OCUPADO, tamanho=TamanhoArmario.PEQUENO
        ),
        Armario(
            numero="11", status=StatusArmario.DISPONIVEL, tamanho=TamanhoArmario.MEDIO
        ),
        Armario(
            numero="12", status=StatusArmario.DISPONIVEL, tamanho=TamanhoArmario.GRANDE
        ),
    ]
    db_session.add_all(armarios)
    db_session.commit()
    for armario in armarios:
        db_session.refresh(armario)

    reservas = [
        Reserva(
            usuario_id=usuario_id,
            armario_id=armarios[0].id,
            data=date(2026, 8, 1),
            hora=time(10, 0),
            status=StatusReserva.CONCLUIDA,
        ),
        Reserva(
            usuario_id=usuario_id,
            armario_id=armarios[1].id,
            data=date(2026, 8, 15),
            hora=time(11, 0),
            status=StatusReserva.CANCELADA,
        ),
        Reserva(
            usuario_id=usuario_id,
            armario_id=armarios[2].id,
            data=date(2026, 9, 1),
            hora=time(12, 0),
            status=StatusReserva.CONCLUIDA,
        ),
        Reserva(
            usuario_id=usuario_id,
            armario_id=armarios[0].id,
            data=date(2099, 9, 5),  # futura: segue ATIVA com a expiração sob demanda
            hora=time(9, 0),
            status=StatusReserva.ATIVA,
        ),
    ]
    db_session.add_all(reservas)
    db_session.commit()


def test_historico_sem_filtro_exclui_ativa(
    client: TestClient,
    db_session: Session,
    usuario: Usuario,
    auth_headers: dict[str, str],
) -> None:
    _seed_historico(db_session, usuario.id)

    resposta = client.get("/reservations/me/history", headers=auth_headers)

    corpo = resposta.json()
    assert corpo["total"] == 3
    assert all(item["status"] != "active" for item in corpo["items"])


def test_historico_filtro_status(
    client: TestClient,
    db_session: Session,
    usuario: Usuario,
    auth_headers: dict[str, str],
) -> None:
    _seed_historico(db_session, usuario.id)

    resposta = client.get(
        "/reservations/me/history",
        params={"status": "completed"},
        headers=auth_headers,
    )

    corpo = resposta.json()
    assert corpo["total"] == 2
    assert all(item["status"] == "completed" for item in corpo["items"])


def test_historico_filtro_search(
    client: TestClient,
    db_session: Session,
    usuario: Usuario,
    auth_headers: dict[str, str],
) -> None:
    _seed_historico(db_session, usuario.id)

    resposta = client.get(
        "/reservations/me/history", params={"search": "11"}, headers=auth_headers
    )

    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["locker_number"] == "11"


def test_historico_filtro_data(
    client: TestClient,
    db_session: Session,
    usuario: Usuario,
    auth_headers: dict[str, str],
) -> None:
    _seed_historico(db_session, usuario.id)

    resposta = client.get(
        "/reservations/me/history",
        params={"start_date": "2026-08-01", "end_date": "2026-08-31"},
        headers=auth_headers,
    )

    corpo = resposta.json()
    assert corpo["total"] == 2


def test_historico_filtro_combinado(
    client: TestClient,
    db_session: Session,
    usuario: Usuario,
    auth_headers: dict[str, str],
) -> None:
    _seed_historico(db_session, usuario.id)

    resposta = client.get(
        "/reservations/me/history",
        params={
            "status": "completed",
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
        },
        headers=auth_headers,
    )

    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["date"] == "2026-08-01"


def test_historico_paginacao(
    client: TestClient,
    db_session: Session,
    usuario: Usuario,
    auth_headers: dict[str, str],
) -> None:
    _seed_historico(db_session, usuario.id)

    resposta = client.get(
        "/reservations/me/history",
        params={"limit": 1, "offset": 1},
        headers=auth_headers,
    )

    corpo = resposta.json()
    assert corpo["total"] == 3
    assert len(corpo["items"]) == 1


def test_historico_vazio(
    client: TestClient, usuario: Usuario, auth_headers: dict[str, str]
) -> None:
    resposta = client.get("/reservations/me/history", headers=auth_headers)

    corpo = resposta.json()
    assert corpo["total"] == 0
    assert corpo["items"] == []


def test_historico_sem_token(client: TestClient) -> None:
    resposta = client.get("/reservations/me/history")

    assert resposta.status_code == 401


def test_me_sem_filtro(
    client: TestClient,
    db_session: Session,
    usuario: Usuario,
    auth_headers: dict[str, str],
) -> None:
    _seed_historico(db_session, usuario.id)

    resposta = client.get("/reservations/me", headers=auth_headers)

    assert resposta.status_code == 200
    assert len(resposta.json()) == 4


def test_me_filtro_active(
    client: TestClient,
    db_session: Session,
    usuario: Usuario,
    auth_headers: dict[str, str],
) -> None:
    _seed_historico(db_session, usuario.id)

    resposta = client.get(
        "/reservations/me", params={"status": "active"}, headers=auth_headers
    )

    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["status"] == "active"


def test_me_sem_reservas(client: TestClient, auth_headers: dict[str, str]) -> None:
    resposta = client.get("/reservations/me", headers=auth_headers)

    assert resposta.json() == []


def test_me_sem_token(client: TestClient) -> None:
    resposta = client.get("/reservations/me")

    assert resposta.status_code == 401
