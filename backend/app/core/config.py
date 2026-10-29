from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Locky"
    database_url: str = "postgresql+psycopg://locky:locky@localhost:5432/locky"
    cors_origins: list[str] = ["http://localhost:5173"]
    secret_key: str = "dev-secret-trocar-em-producao"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    tempo_maximo_reserva_minutos: int = 120
    expiracao_intervalo_minutos: int = 5
    seed_admin_email: str = "admin@locky.com"
    seed_admin_password: str = "admin123"


settings = Settings()
