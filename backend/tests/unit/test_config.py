import pytest
from pydantic import ValidationError

from app.core.config import SECRET_KEY_DESENVOLVIMENTO, Settings

CHAVE_FORTE = "x" * 48


def test_dev_aceita_chave_padrao() -> None:
    assert Settings(env="dev", _env_file=None).secret_key == SECRET_KEY_DESENVOLVIMENTO  # type: ignore[call-arg]


def test_prod_recusa_chave_padrao() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY padrão"):
        Settings(env="prod", secret_key=SECRET_KEY_DESENVOLVIMENTO, _env_file=None)  # type: ignore[call-arg]


def test_prod_recusa_chave_curta() -> None:
    with pytest.raises(ValidationError, match="pelo menos 32 bytes"):
        Settings(env="prod", secret_key="curta", _env_file=None)  # type: ignore[call-arg]


def test_prod_aceita_chave_forte() -> None:
    assert Settings(env="prod", secret_key=CHAVE_FORTE, _env_file=None).env == "prod"  # type: ignore[call-arg]


def test_url_do_provedor_ganha_driver_psycopg() -> None:
    for url in (
        "postgres://u:s@host/db?sslmode=require",
        "postgresql://u:s@host/db?sslmode=require",
    ):
        config = Settings(database_url=url, _env_file=None)  # type: ignore[call-arg]
        assert config.database_url == "postgresql+psycopg://u:s@host/db?sslmode=require"


def test_url_com_driver_e_mantida() -> None:
    url = "postgresql+psycopg://u:s@host/db"
    assert Settings(database_url=url, _env_file=None).database_url == url  # type: ignore[call-arg]


def test_fuso_horario_invalido() -> None:
    with pytest.raises(ValidationError, match="Fuso horário inválido"):
        Settings(fuso_horario="Marte/Olympus", _env_file=None)  # type: ignore[call-arg]


def test_scheduler_desligado_em_serverless(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    config = Settings(_env_file=None)  # type: ignore[call-arg]

    assert config.serverless is True
    assert config.executar_scheduler is False


def test_scheduler_ligado_fora_do_serverless(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VERCEL", raising=False)
    config = Settings(_env_file=None)  # type: ignore[call-arg]

    assert config.executar_scheduler is True
    assert (
        Settings(scheduler_habilitado=False, _env_file=None).executar_scheduler is False
    )  # type: ignore[call-arg]
