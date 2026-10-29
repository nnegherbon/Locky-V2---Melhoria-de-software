# Relatório Formal de Handoff - Projeto Locky (N2)

## 1. Identificação

- **Projeto**: Locky (Sistema de Gestão e Reserva de Armários de Academia)
- **Repositório (N2)**: [github.com/ruanplp123/Manutencao-e-melhoria](https://github.com/ruanplp123/Manutencao-e-melhoria)
- **Repositório de origem (N1)**: [github.com/mari-catolicasc/locky](https://github.com/mari-catolicasc/locky). O histórico de commits da N1 foi preservado no repositório da N2
- **Versão entregue**: `v2.0` (N2) · versão anterior: `1.0.0` (N1)

| Fase | Equipe | PO |
| :--- | :--- | :--- |
| N1 (origem) | Cartel / Locky Team | Leonardo Lima |
| N2 (receptora) | **[nome da equipe]** | **[nome do PO]** |

**Sistema publicado:** [https://locky-web.vercel.app](https://locky-web.vercel.app) ·
API: [https://locky-api.vercel.app/docs](https://locky-api.vercel.app/docs) *(ajustar se os
domínios forem outros)*

A matriz de papéis e o histórico de contribuições de cada fase estão no
[README](../README.md).

---

## 2. Parecer de recepção da N2 (sobre o que recebemos da N1)

**Viável, com correções obrigatórias.** O backend era sólido (camadas bem separadas,
100% de cobertura, concorrência tratada), mas o sistema **não funcionava de ponta a
ponta** em uma instalação nova:

- não havia como criar usuários (sem cadastro na API e sem seed);
- as telas de Cadastro e de Administração eram simuladas no frontend;
- a documentação descrevia banco, rotas, porta e esquema diferentes dos reais.

O diagnóstico completo, as decisões e a justificativa de cada mudança estão em
[`melhorias-n2.md`](melhorias-n2.md).

---

## 3. Arquitetura

```
Frontend (React 19 + TypeScript + Vite)          :5173
  pages/ → services/ (Axios) → context/AuthContext
                    │  HTTP REST / JSON, Bearer JWT
                    ▼
Backend (FastAPI, Python 3.12)                   :8080
  api/ (rotas, autenticação e autorização)
   → services/ (regras de negócio)
   → repositories/ (consultas SQLAlchemy)
   → models/ (ORM)
  core/scheduler.py: APScheduler expira reservas vencidas (desligado no Vercel;
                     lá a expiração ocorre sob demanda em api/deps.py)
                    │
                    ▼
PostgreSQL 16 (docker compose)                   :5432 (dev) / :5433 (testes)
  migrations versionadas com Alembic
```

---

## 4. Como executar do zero

Pré-requisitos: Python 3.12, [uv](https://docs.astral.sh/uv/), Docker, Node.js 22.

```bash
# Backend
cd backend
uv sync
cp .env.example .env
docker compose up -d db
uv run alembic upgrade head
uv run python -m app.seed          # cria admin e 12 armários (idempotente)
uv run uvicorn app.main:app --reload --port 8080

# Frontend (outro terminal)
cd frontend
cp .env.example .env               # VITE_API_URL=http://localhost:8080
npm install
npm run dev                        # http://localhost:5173
```

**Acesso inicial:** `admin@locky.com` / `admin123` (configurável por
`SEED_ADMIN_EMAIL` e `SEED_ADMIN_PASSWORD`). Contas de associado são criadas pela tela
de cadastro.

**Produção (Vercel + Neon):** passo a passo em [`deploy-vercel.md`](deploy-vercel.md).
Migrations e seed de produção rodam pelo workflow manual *Migrations de produção*.

---

## 5. Contrato da API

Swagger UI em `http://localhost:8080/docs`. O contrato exportado está em
[`docs/api/openapi.json`](api/openapi.json) e pode ser importado no Postman
(*Import → File*).

| Método | Endpoint | Descrição | Acesso |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Verifica se a API está no ar | Público |
| `POST` | `/auth/register` | Cria conta de associado **(N2)** | Público |
| `POST` | `/auth/login` | Retorna token JWT | Público |
| `GET` | `/auth/me` | Dados do usuário logado | Autenticado |
| `GET` | `/lockers` | Lista armários (filtros `status`, `size`; `limit`/`offset`) | Autenticado |
| `GET` | `/lockers/stats` | Contagem por status, incluindo `maintenance` **(N2)** | Autenticado |
| `POST` | `/lockers` | Cadastra armário **(N2)** | Admin |
| `PATCH` | `/lockers/{id}` | Edita número, tamanho e status disponível/manutenção **(N2)** | Admin |
| `DELETE` | `/lockers/{id}` | Exclui armário sem histórico **(N2)** | Admin |
| `POST` | `/reservations` | Cria reserva | Autenticado |
| `GET` | `/reservations/me` | Reservas do usuário (filtro `status`) | Autenticado |
| `GET` | `/reservations/me/history` | Histórico paginado com busca e período | Autenticado |
| `PATCH` | `/reservations/{id}/cancel` | Cancela reserva ativa do próprio usuário | Autenticado |

Erros seguem o formato `{ "detail": "mensagem" }` com 401 (não autenticado),
403 (sem permissão), 404, 409 (conflito de regra de negócio) e 422 (validação).

---

## 6. Qualidade

- **CI (GitHub Actions):** backend roda `ruff check`, `ruff format --check`,
  `mypy --strict`, migrations e `pytest` com **cobertura mínima de 100%**; frontend
  roda `eslint` e `tsc + vite build`. O workflow manual `migrate-producao.yml` aplica
  migrations e seed no banco de produção.
- **Testes locais:** `cd backend && uv run pytest` (124 testes). O teste de
  concorrência precisa de `docker compose up -d db_test`; sem ele, é pulado.
- **Roteiro manual de QA:** seção 5 de [`melhorias-n2.md`](melhorias-n2.md).

---

## 7. Recomendações para a próxima equipe

Em ordem de prioridade (detalhes em [`debitos-tecnicos.md`](debitos-tecnicos.md)):

1. **DT-09:** limitar tentativas de login antes de qualquer publicação.
2. **DT-06:** definir com o PO a antecedência máxima da reserva e implementar o
   check-in (`RESERVADO → OCUPADO`).
3. **DT-07:** padronizar datas com fuso horário (exige migration).
4. **DT-04:** testes E2E do frontend (Playwright), cobrindo o roteiro manual.
5. **DT-02:** refresh token para renovação silenciosa da sessão.
