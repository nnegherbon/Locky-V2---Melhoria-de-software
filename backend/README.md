# Locky — Backend

API de gestão de reservas de armários de academia, construída com FastAPI.

## Stack

- **FastAPI** + Uvicorn
- **SQLAlchemy 2.0** + Alembic (migrations)
- **PostgreSQL**
- **Pydantic v2** / pydantic-settings
- **uv** (gerenciador de pacotes)
- **ruff** (lint + format), **mypy --strict**, **pytest** (cobertura 100%)

## Requisitos

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker (para o Postgres via `docker-compose`)

## Setup

```bash
# instalar dependências
uv sync

# variáveis de ambiente
cp .env.example .env

# subir o banco
docker compose up -d db

# aplicar migrations
uv run alembic upgrade head

# criar admin (admin@locky.com / admin123) e 12 armários — idempotente
uv run python -m app.seed

# rodar a API (http://localhost:8080)
uv run uvicorn app.main:app --reload --port 8080
```

## Variáveis de ambiente

Ver `.env.example`. As principais:

| Variável | Padrão | Observação |
|---|---|---|
| `ENV` | `dev` | Com `prod`, a API não sobe se `SECRET_KEY` for a padrão ou tiver menos de 32 bytes |
| `SECRET_KEY` | chave de desenvolvimento | Assina os tokens JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `120` | Validade do token |
| `TEMPO_MAXIMO_RESERVA_MINUTOS` | `120` | Duração de uma reserva a partir de data + hora |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | `admin@locky.com` / `admin123` | Usados por `python -m app.seed` |

## Qualidade

```bash
uv run ruff check .        # lint
uv run ruff format .       # format
uv run mypy app            # tipos (strict)
uv run pytest              # testes + cobertura 100%
```

### Teste de concorrência (lock de reserva)

`tests/integration/test_reservas_concorrencia.py` valida com um banco Postgres real
(threads + `SELECT ... FOR UPDATE`) que duas requisições simultâneas para o mesmo
armário resultam em só uma reserva — SQLite não simula lock de linha de verdade,
por isso esse teste não usa a fixture padrão em memória. Sobe automaticamente com o
resto da suíte se o banco de teste estiver de pé; senão, pula (`skip`) com um aviso.

```bash
docker compose up -d db_test   # Postgres dedicado, porta 5433
uv run pytest tests/integration/test_reservas_concorrencia.py
```

## Estrutura

```
app/
  api/          # routers (endpoints)
  core/         # config, db, security, scheduler, erros
  seed.py       # dados iniciais (admin + armários)
  models/       # models SQLAlchemy
  schemas/      # schemas Pydantic (request/response)
  services/     # regras de negócio
  repositories/ # acesso a dados
tests/
  unit/
  integration/
```
