from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Chave apenas para desenvolvimento local. Em qualquer outro ambiente a aplicação
# se recusa a subir com ela, porque quem conhece a chave consegue forjar tokens.
SECRET_KEY_DESENVOLVIMENTO = "dev-secret-trocar-em-producao-locky"
SECRET_KEY_TAMANHO_MINIMO = 32  # bytes recomendados para HS256 (RFC 7518 §3.2)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Locky"
    env: Literal["dev", "test", "prod"] = "dev"
    database_url: str = "postgresql+psycopg://locky:locky@localhost:5432/locky"
    cors_origins: list[str] = ["http://localhost:5173"]
    secret_key: str = SECRET_KEY_DESENVOLVIMENTO
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    tempo_maximo_reserva_minutos: int = 120
    expiracao_intervalo_minutos: int = 5
    seed_admin_email: str = "admin@locky.com"
    seed_admin_password: str = "admin123"

    @model_validator(mode="after")
    def exigir_chave_segura_fora_do_dev(self) -> Self:
        if self.env == "prod":
            if self.secret_key == SECRET_KEY_DESENVOLVIMENTO:
                raise ValueError(
                    "SECRET_KEY padrão não pode ser usada em produção. "
                    "Defina SECRET_KEY no ambiente."
                )
            if len(self.secret_key.encode()) < SECRET_KEY_TAMANHO_MINIMO:
                raise ValueError(
                    f"SECRET_KEY deve ter pelo menos {SECRET_KEY_TAMANHO_MINIMO} bytes."
                )
        return self


settings = Settings()
