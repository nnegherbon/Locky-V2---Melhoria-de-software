from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Armario, StatusArmario, TamanhoArmario


def _seed(db_session: Session) -> None:
    db_session.add_all(
        [
            Armario(
                numero="01",
                status=StatusArmario.DISPONIVEL,
                tamanho=TamanhoArmario.PEQUENO,
            ),
            Armario(
                numero="02", status=StatusArmario.OCUPADO, tamanho=TamanhoArmario.MEDIO
            ),
            Armario(
                numero="03",
                status=StatusArmario.RESERVADO,
                tamanho=TamanhoArmario.GRANDE,
            ),
            Armario(
                numero="04",
                status=StatusArmario.DISPONIVEL,
                tamanho=TamanhoArmario.MEDIO,
            ),
            Armario(
                numero="05",
                status=StatusArmario.MANUTENCAO,
                tamanho=TamanhoArmario.PEQUENO,
            ),
        ]
    )
    db_session.commit()


def test_listar_sem_filtro(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    _seed(db_session)

    resposta = client.get("/lockers", headers=auth_headers)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 5
    assert len(corpo["items"]) == 5


def test_listar_filtro_por_status(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    _seed(db_session)

    resposta = client.get(
        "/lockers", params={"status": "available"}, headers=auth_headers
    )

    corpo = resposta.json()
    assert corpo["total"] == 2
    assert all(item["status"] == "available" for item in corpo["items"])


def test_listar_filtro_por_size(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    _seed(db_session)

    resposta = client.get("/lockers", params={"size": "medium"}, headers=auth_headers)

    corpo = resposta.json()
    assert corpo["total"] == 2
    assert all(item["size"] == "medium" for item in corpo["items"])


def test_listar_filtro_combinado(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    _seed(db_session)

    resposta = client.get(
        "/lockers",
        params={"status": "available", "size": "medium"},
        headers=auth_headers,
    )

    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["number"] == "04"


def test_listar_paginacao(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    _seed(db_session)

    resposta = client.get(
        "/lockers", params={"limit": 2, "offset": 1}, headers=auth_headers
    )

    corpo = resposta.json()
    assert corpo["total"] == 5
    assert corpo["limit"] == 2
    assert corpo["offset"] == 1
    assert len(corpo["items"]) == 2
    assert [item["number"] for item in corpo["items"]] == ["02", "03"]


def test_listar_pagina_vazia(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    _seed(db_session)

    resposta = client.get("/lockers", params={"offset": 100}, headers=auth_headers)

    corpo = resposta.json()
    assert corpo["total"] == 5
    assert corpo["items"] == []


def test_listar_sem_token(client: TestClient, db_session: Session) -> None:
    _seed(db_session)

    resposta = client.get("/lockers")

    assert resposta.status_code == 401


def test_stats_com_dados(
    client: TestClient, db_session: Session, auth_headers: dict[str, str]
) -> None:
    _seed(db_session)

    resposta = client.get("/lockers/stats", headers=auth_headers)

    assert resposta.status_code == 200
    assert resposta.json() == {
        "total": 5,
        "available": 2,
        "reserved": 1,
        "occupied": 1,
        "maintenance": 1,
    }


def test_stats_sem_armarios(client: TestClient, auth_headers: dict[str, str]) -> None:
    resposta = client.get("/lockers/stats", headers=auth_headers)

    assert resposta.status_code == 200
    assert resposta.json() == {
        "total": 0,
        "available": 0,
        "reserved": 0,
        "occupied": 0,
        "maintenance": 0,
    }
