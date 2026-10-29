from datetime import timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.clock import agora_local
from app.models import Armario


def test_agora_local_usa_fuso_configurado_e_nao_o_do_servidor() -> None:
    with patch("app.core.clock.settings.fuso_horario", "UTC"):
        agora_utc = agora_local()
    agora_sp = agora_local()  # padrão: America/Sao_Paulo (UTC-3, sem horário de verão)

    diferenca = agora_utc - agora_sp
    assert timedelta(hours=2, minutes=59) < diferenca < timedelta(hours=3, minutes=1)
    assert agora_sp.tzinfo is None


def test_reserva_daqui_a_30_min_no_horario_local_e_aceita(
    client: TestClient, armario_disponivel: Armario, auth_headers: dict[str, str]
) -> None:
    # Regressão do deploy: com o servidor em UTC, datetime.now() estaria 3h à
    # frente de São Paulo e recusaria esta reserva como "no passado".
    daqui_a_pouco = agora_local() + timedelta(minutes=30)

    resposta = client.post(
        "/reservations",
        json={
            "locker_id": armario_disponivel.id,
            "date": daqui_a_pouco.date().isoformat(),
            "time": daqui_a_pouco.time().isoformat(timespec="minutes"),
        },
        headers=auth_headers,
    )

    assert resposta.status_code == 201
