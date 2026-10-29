from datetime import timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.clock import agora_local
from app.core.config import settings
from app.models import Armario, Reserva, StatusArmario, StatusReserva, Usuario
from app.services.reservation_service import expirar_reservas_vencidas


def _reserva_vencida(
    db_session: Session, usuario: Usuario, armario: Armario
) -> Reserva:
    inicio = agora_local() - timedelta(
        minutes=settings.tempo_maximo_reserva_minutos + 5
    )
    reserva = Reserva(
        usuario_id=usuario.id,
        armario_id=armario.id,
        data=inicio.date(),
        hora=inicio.time(),
        status=StatusReserva.ATIVA,
    )
    armario.status = StatusArmario.RESERVADO
    db_session.add(reserva)
    db_session.commit()
    db_session.refresh(reserva)
    return reserva


def test_listar_armarios_libera_reserva_vencida_sem_scheduler(
    client: TestClient,
    db_session: Session,
    usuario: Usuario,
    auth_headers: dict[str, str],
    armario_disponivel: Armario,
) -> None:
    reserva = _reserva_vencida(db_session, usuario, armario_disponivel)

    resposta = client.get("/lockers", headers=auth_headers)

    assert resposta.json()["items"][0]["status"] == "available"
    db_session.refresh(reserva)
    assert reserva.status == StatusReserva.CONCLUIDA


def test_usuario_pode_reservar_de_novo_apos_vencer(
    client: TestClient,
    db_session: Session,
    usuario: Usuario,
    auth_headers: dict[str, str],
    armario_disponivel: Armario,
) -> None:
    _reserva_vencida(db_session, usuario, armario_disponivel)
    amanha = (agora_local() + timedelta(days=1)).date().isoformat()

    resposta = client.post(
        "/reservations",
        json={"locker_id": armario_disponivel.id, "date": amanha, "time": "10:00"},
        headers=auth_headers,
    )

    assert resposta.status_code == 201


def test_falha_na_expiracao_nao_derruba_a_requisicao(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    with patch(
        "app.api.deps.expirar_reservas_vencidas",
        side_effect=OperationalError("select", {}, Exception("banco lento")),
    ):
        resposta = client.get("/lockers", headers=auth_headers)

    assert resposta.status_code == 200


def test_sem_reservas_vencidas_nada_e_alterado(
    db_session: Session, usuario: Usuario, armario_disponivel: Armario
) -> None:
    assert expirar_reservas_vencidas(db_session) == 0


def test_reserva_tratada_por_requisicao_concorrente_e_ignorada(
    db_session: Session, usuario: Usuario, armario_disponivel: Armario
) -> None:
    reserva = _reserva_vencida(db_session, usuario, armario_disponivel)
    # Outra requisição cancelou a reserva entre a leitura e o lock.
    reserva.status = StatusReserva.CANCELADA
    db_session.commit()

    with patch(
        "app.services.reservation_service.reserva_repository.listar_ativas",
        return_value=[reserva],
    ):
        total = expirar_reservas_vencidas(db_session)

    assert total == 0
    db_session.refresh(reserva)
    assert reserva.status == StatusReserva.CANCELADA
