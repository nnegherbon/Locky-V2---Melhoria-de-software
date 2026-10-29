# Locky — Sistema de Gestão de Reservas de Armários

O **Locky** é uma aplicação web para reserva de armários em academias: o associado
consulta os armários disponíveis, reserva, cancela e acompanha o histórico; o
administrador cadastra, edita e coloca armários em manutenção. Reservas vencidas são
liberadas automaticamente.

| | |
| :--- | :--- |
| **Versão atual** | `v2.0` (N2) — [o que mudou](docs/melhorias-n2.md) |
| **Repositório** | [nnegherbon/Locky-V2---Melhoria-de-software](https://github.com/nnegherbon/Locky-V2---Melhoria-de-software) · origem N1: [mari-catolicasc/locky](https://github.com/mari-catolicasc/locky) |
| **Backend** | Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL 16 · JWT |
| **Frontend** | React 19 · TypeScript · Vite · React Router · Axios |
| **Publicação** | Vercel (frontend + API serverless) + Neon PostgreSQL — [guia de deploy](docs/deploy-vercel.md) |
| **Qualidade** | pytest (124 testes, cobertura 100%) · ruff · mypy strict · ESLint · GitHub Actions |

---

## 🚀 Como executar do zero

Pré-requisitos: Python 3.12, [uv](https://docs.astral.sh/uv/), Docker e Node.js 22.

### 1. Backend (http://localhost:8080)

```bash
cd backend
uv sync                              # instala dependências
cp .env.example .env                 # Windows: copy .env.example .env
docker compose up -d db              # PostgreSQL na porta 5432
uv run alembic upgrade head          # cria as tabelas
uv run python -m app.seed            # cria o admin e 12 armários (pode rodar de novo)
uv run uvicorn app.main:app --reload --port 8080
```

- Swagger UI: http://localhost:8080/docs (a raiz `/` não tem rota, é esperado ver `Not Found`)
- Contrato exportado para Postman: [`docs/api/openapi.json`](docs/api/openapi.json)

<details>
<summary>Sem o uv (Windows, com pip)</summary>

```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install fastapi "uvicorn[standard]" sqlalchemy alembic "psycopg[binary]" pydantic pydantic-settings pyjwt bcrypt email-validator apscheduler
copy .env.example .env
docker compose up -d db
.venv\Scripts\alembic upgrade head
.venv\Scripts\python -m app.seed
.venv\Scripts\uvicorn app.main:app --reload --port 8080
```
</details>

### 2. Frontend (http://localhost:5173)

```bash
cd frontend
cp .env.example .env                 # VITE_API_URL=http://localhost:8080
npm install
npm run dev
```

### 3. Acesso

| Perfil | Como obter |
| :--- | :--- |
| Administrador | `admin@locky.com` / `admin123`, criado pelo seed (mude em `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD`) |
| Associado | Tela **Criar conta** (`/register`) |

> **Produção:** siga [`docs/deploy-vercel.md`](docs/deploy-vercel.md). Com `ENV=prod`, a API
> recusa a `SECRET_KEY` padrão e o seed recusa a senha padrão do admin.

---

## 🧪 Testes e verificações

```bash
# Backend (mesmos passos do CI)
cd backend
uv run ruff check . && uv run ruff format --check .
uv run mypy app
uv run pytest                        # exige cobertura de 100%

# Teste de concorrência com PostgreSQL real (opcional localmente; roda no CI)
docker compose up -d db_test

# Frontend
cd frontend
npm run lint
npm run build
```

Roteiro de teste manual (QA): seção 5 de [`docs/melhorias-n2.md`](docs/melhorias-n2.md).

---

## 📁 Documentação (`docs/`)

| Documento | Conteúdo |
| :--- | :--- |
| [`DER.md`](docs/DER.md) | Modelo de dados real, dicionário, índices e ciclo de vida (revisado na N2) |
| [`debitos-tecnicos.md`](docs/debitos-tecnicos.md) | Política, inventário N1 e novos débitos da N2 (DT-06 a DT-11) |
| [`handoff.md`](docs/handoff.md) | Parecer de recepção, arquitetura, execução, endpoints e recomendações |
| [`melhorias-n2.md`](docs/melhorias-n2.md) | Diagnóstico, decisões técnicas e justificativas das mudanças da N2 |
| [`deploy-vercel.md`](docs/deploy-vercel.md) | Passo a passo do deploy no Vercel + Neon e solução de problemas |
| [`api/openapi.json`](docs/api/openapi.json) | Contrato OpenAPI 3 (importar no Postman: *Import → File*) |
| [`regras-negocio-contrato-api.md`](docs/regras-negocio-contrato-api.md) | Regras de negócio e contrato proposto na N1 |
| [`Acordo de Manutenibilidade`](docs/Acordo%20de%20Manutenibilidade%20e%20Engenharia%20de%20So.docx) | Combinados de engenharia da equipe |

---

## 📋 Matriz de Papéis e Histórico de Contribuições

O papel atribuído a cada integrante indica sua responsabilidade principal, não
exclusividade sobre a área.

### N2 — Equipe receptora ([nome da equipe])

> **A preencher pela equipe:** uma linha por integrante com as atividades
> efetivamente realizadas na N2 e links para as evidências (PRs, commits, cards).

| Integrante | Papel Principal | Principais Atividades Realizadas (N2) | Evidências / Artefatos |
| :--- | :--- | :--- | :--- |
| [nome] | Product Owner (PO) | Diagnóstico de recepção e priorização das melhorias; definição das regras do módulo admin (RN-A1 a RN-A4) | [`melhorias-n2.md`](docs/melhorias-n2.md), board de tarefas |
| [nome] | Desenvolvedor(a) Backend | Cadastro de usuário, seed, endpoints administrativos com `require_admin`, validação da `SECRET_KEY` | Commits `N2-01`, `N2-02`, `N2-03` |
| [nome] | Desenvolvedor(a) Frontend | Tela de cadastro integrada, tela de administração integrada, tratamento de sessão expirada | Commits `N2-01`, `N2-02`, `N2-03` |
| [nome] | Quality Assurance (QA) | Roteiro de teste manual, validação dos 12 cenários, revisão dos testes automatizados | Seção 5 de `melhorias-n2.md` |
| [nome] | Engenheiro(a) de Requisitos | Revisão das regras de negócio e do DER contra o código real | [`DER.md`](docs/DER.md), [`debitos-tecnicos.md`](docs/debitos-tecnicos.md) |
| [nome] | DevOps | Branches e PRs, CI, deploy no Vercel + Neon, workflow de migrations, tag `v2.0` | Release `v2.0`, `docs/deploy-vercel.md`, `.github/workflows/` |

### N1 — Equipe de origem (Cartel / Locky Team)

| Integrante | Papel Principal | Principais Atividades Realizadas (N1) | Evidências / Artefatos |
| :--- | :--- | :--- | :--- |
| **Leonardo Lima** | **Product Owner (PO)** | Definção do backlog, refinamento dos critérios de aceite, gestão do escopo da N1, estruturação dos artefatos de entrega e liderança da apresentação do Pitch. | Issue tracking, [docs/PITCH_ROTEIRO_PO.md](docs/PITCH_ROTEIRO_PO.md), [docs/handoff.md](docs/handoff.md). |
| **Marina** | **DevOps** | Elaboração do diário de bordo, gestão do repositório GitHub, acompanhamento de entregas, revisão de PRs, criação de acordos de manutenibilidade e governança das releases. | Pull Requests #1 a #5, #12, branch management, `Acordo de Manutenibilidade e Engenharia de So.docx`. |
| **Miguel Dufloth** | **Backend Developer** | Desenvolvimento da API REST em FastAPI, autenticação JWT, modelagem de banco de dados (SQLAlchemy + Alembic), regras de concorrência e testes automatizados. | Commits L8-L15, `backend/app/`, suíte `pytest` (20+ testes). |
| **Lucas Honorato** | **Frontend Developer** | Construção da interface web em React com TypeScript e Vite, telas de Login, Dashboard, Armários e Reservas, e integração com os endpoints REST. | Commits L4 e L16, `frontend/src/`, `frontend-ci.yml`. |
| **Ana Júlia** | **Quality Assurance (QA)** | Testes funcionais, validação de regras de negócio, reporte de bugs de concorrência/interface e verificação de critérios de aceite. | Commit L17 (`fix/l17-corrige-achados-qa`), relatórios de testes. |
| **Miguel Huertas** | **Engenheiro de Requisitos** | Auxílio na preparação de materiais visuais e suporte na síntese dos encontros da disciplina. | `regras-negocio-contrato-api.md`, relatórios de aula. |

---

## 📌 DoR e DoD (Definition of Ready & Definition of Done)

### Definition of Ready (DoR) — Uma issue está pronta para desenvolvimento quando:
1. Tem um título claro seguindo o padrão de nomenclatura.
2. Contém a descrição do problema ou da funcionalidade esperada.
3. Possui os **Critérios de Aceite** definidos e testáveis.
4. Foi estimada pela equipe e priorizada no backlog pelo Product Owner.
5. Não possui bloqueios pendentes de outras atividades.

### Definition of Done (DoD) — Uma tarefa é considerada concluída quando:
1. O código foi implementado seguindo o guia de estilo do projeto.
2. Foram criados ou atualizados os testes automatizados correspondentes.
3. O código passa sem erros no pipeline de CI (lint e testes).
4. O Pull Request foi revisado e aprovado por pelo menos um integrante da equipe.
5. As alterações foram mescladas na branch `dev`.
6. A documentação (DER, endpoints ou README) foi atualizada, se aplicável.

---

## 🌿 Versionamento e Padronização

### Nomenclatura de Branches
- `feature/nome-da-funcionalidade` — Novas funcionalidades.
- `fix/nome-da-correcao` — Correção de bugs.
- `docs/nome-da-documentacao` — Alterações em documentação.
- `refactor/nome-do-debito` — Quitação de débitos técnicos.

### Nomenclatura de Commits
Todos os commits devem seguir o padrão:
`NOME-DA-ISSUE - breve descrição do que foi feito`

---
