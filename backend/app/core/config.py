import os
from typing import Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator
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
    # Ex.: https://locky-.*\.vercel\.app para aceitar também os deploys de preview.
    cors_origin_regex: str | None = None
    secret_key: str = SECRET_KEY_DESENVOLVIMENTO
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    tempo_maximo_reserva_minutos: int = 120
    expiracao_intervalo_minutos: int = 5
    # Data/hora das reservas são interpretadas no horário da academia, não no do
    # servidor (no Vercel os servidores ficam em UTC).
    fuso_horario: str = "America/Sao_Paulo"
    scheduler_habilitado: bool = True
    # O Vercel define VERCEL=1 nas funções. Em serverless não há processo contínuo
    # para o scheduler e cada invocação deve abrir/fechar sua conexão.
    serverless: bool = Field(default_factory=lambda: bool(os.getenv("VERCEL")))
    seed_admin_email: str = "admin@locky.com"
    seed_admin_password: str = "admin123"  # recusada pelo seed quando ENV=prod

    @field_validator("database_url")
    @classmethod
    def usar_driver_psycopg(cls, valor: str) -> str:
        """Aceita a URL no formato dos provedores (postgres:// ou postgresql://).

        Neon, Vercel Postgres, Render etc. entregam a URL sem driver; o SQLAlchemy
        assumiria psycopg2, que não está instalado. O projeto usa psycopg 3.
        """
        for prefixo in ("postgres://", "postgresql://"):
            if valor.startswith(prefixo):
                return "postgresql+psycopg://" + valor.removeprefix(prefixo)
        return valor

    @field_validator("fuso_horario")
    @classmethod
    def validar_fuso(cls, valor: str) -> str:
        try:
            ZoneInfo(valor)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"Fuso horário inválido: {valor}") from exc
        return valor

    @property
    def executar_scheduler(self) -> bool:
        return self.scheduler_habilitado and not self.serverless

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
