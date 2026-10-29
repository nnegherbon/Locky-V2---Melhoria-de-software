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
