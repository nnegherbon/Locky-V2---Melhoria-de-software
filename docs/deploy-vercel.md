# Deploy no Vercel

O Locky é publicado como **dois projetos Vercel apontando para o mesmo repositório**,
mais um banco PostgreSQL gerenciado (Neon):

```
 Navegador ──▶ locky-web  (Root Directory: frontend/, preset Vite, site estático)
                   │  HTTPS + JWT
                   ▼
              locky-api  (Root Directory: backend/, preset FastAPI, função serverless)
                   │
                   ▼
              Neon PostgreSQL (integração do Vercel Marketplace)
```

**Por que dois projetos?** Cada parte usa o preset oficial e estável do Vercel
(Vite e FastAPI). Juntar tudo num projeto só exigiria o recurso *Services*, que ainda
está em beta.

> Tempo estimado: 20 a 30 minutos. É preciso ser **dono ou admin do repositório** no
> GitHub (para conectar ao Vercel e criar os segredos do Actions).

---

## O que muda no Vercel em relação ao ambiente local

| Ponto | Local | Vercel | Onde foi tratado |
| :--- | :--- | :--- | :--- |
| Expiração de reservas | Scheduler a cada 5 min | Não há processo contínuo e o cron gratuito roda só 1×/dia: a expiração acontece **no início de cada requisição** de armários/reservas | `api/deps.py::expirar_vencidas` |
| Fuso horário | Servidor no horário local | Servidores em **UTC**: datas são interpretadas em `FUSO_HORARIO` (padrão `America/Sao_Paulo`) | `core/clock.py` |
| Conexões com o banco | Pool de conexões | Sem pool (`NullPool`); usa a URL *pooled* do Neon | `core/db.py` |
| URL do banco | `postgresql+psycopg://...` | Neon entrega `postgresql://...`; convertida automaticamente | `core/config.py` |
| Migrations e seed | `alembic` e `python -m app.seed` no terminal | Workflow manual do GitHub Actions | `.github/workflows/migrate-producao.yml` |
| Segurança | Chave e senha padrão aceitas | `ENV=prod` recusa `SECRET_KEY` padrão/curta e o seed recusa a senha padrão | `core/config.py`, `seed.py` |

---

## Passo 1 · Projeto da API (`locky-api`)

1. No Vercel: **Add New → Project** → importe `mari-catolicasc/locky`.
2. **Project Name:** `locky-api`.
3. **Root Directory:** clique em *Edit* e escolha **`backend`**.
4. **Framework Preset:** deve aparecer **FastAPI** (detectado pelo `pyproject.toml`, que
   já declara `[tool.vercel] entrypoint = "app.main:app"`). Python 3.12 vem do
   `backend/.python-version`.
5. Ainda **não** clique em Deploy: abra **Environment Variables** e adicione:

   | Variável | Valor |
   | :--- | :--- |
   | `ENV` | `prod` |
   | `SECRET_KEY` | gere com `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `CORS_ORIGINS` | `["https://locky-web.vercel.app"]` (ajuste no passo 4 se o domínio for outro) |
   | `CORS_ORIGIN_REGEX` | `https://locky-web-.*\.vercel\.app` (libera os deploys de *preview*) |

   `DATABASE_URL` virá do banco no passo 2. `FUSO_HORARIO` e
   `TEMPO_MAXIMO_RESERVA_MINUTOS` têm padrões adequados e são opcionais.

6. Clique em **Deploy**. A API sobe, mas qualquer rota que use o banco responde erro
   até o passo 2. Isso é esperado.

## Passo 2 · Banco de dados (Neon)

1. No projeto `locky-api`: aba **Storage → Create Database → Neon** (ou instale o Neon
   pelo **Marketplace**).
2. Escolha o plano gratuito e, se disponível, a região **São Paulo (sa-east-1)**.
   Dê o nome `locky-db`.
3. Conecte o banco ao projeto `locky-api` nos ambientes *Production* e *Preview*.
   A integração cria `DATABASE_URL` (com pool) e `DATABASE_URL_UNPOOLED` (direta).
4. Em **Deployments**, abra o último deploy → **⋯ → Redeploy**.
5. Teste: `https://locky-api.vercel.app/health` deve responder `{"status":"ok"}` e
   `https://locky-api.vercel.app/docs` deve abrir o Swagger.

## Passo 3 · Migrations e seed (GitHub Actions)

O Vercel só atende requisições; ele não cria as tabelas.

1. No GitHub: **Settings → Environments → New environment** → nome **`producao`**.
2. Dentro dele, em **Environment secrets**, crie:

   | Segredo | Valor |
   | :--- | :--- |
   | `PRODUCTION_DATABASE_URL` | valor de **`DATABASE_URL_UNPOOLED`** (Vercel → Storage → locky-db → *.env.local*). Migrations devem usar a conexão direta |
   | `PRODUCTION_SECRET_KEY` | a mesma `SECRET_KEY` do passo 1 |
   | `SEED_ADMIN_EMAIL` | e-mail do administrador da demonstração |
   | `SEED_ADMIN_PASSWORD` | senha com **10+ caracteres** (a padrão `admin123` é recusada) |

3. **Actions → Migrations de produção → Run workflow** (branch `main`).
4. O log deve terminar com `Seed concluído: admin criado, 12 armário(s) criado(s).`

Repita só o passo 3 quando uma migration nova for mesclada. Rodar de novo é seguro:
as migrations e o seed são idempotentes.

## Passo 4 · Projeto do frontend (`locky-web`)

1. **Add New → Project** → importe o mesmo repositório.
2. **Project Name:** `locky-web` · **Root Directory:** **`frontend`** · preset **Vite**.
3. **Environment Variables:**

   | Variável | Valor |
   | :--- | :--- |
   | `VITE_API_URL` | `https://locky-api.vercel.app` (sem barra no final) |

   Sem ela o build **falha de propósito** (ver `vite.config.ts`), para não publicar um
   site apontando para `localhost`.
4. **Deploy.** O `frontend/vercel.json` já redireciona todas as rotas para o
   `index.html`, então recarregar em `/dashboard` não dá 404.
5. Se o domínio final não for `https://locky-web.vercel.app`, atualize `CORS_ORIGINS`
   no `locky-api` e faça *Redeploy* da API.

## Passo 5 · Verificação

Rode o roteiro de QA (seção 5 de [`melhorias-n2.md`](melhorias-n2.md)) no site
publicado. Pontos específicos do deploy:

| Verificação | Esperado |
| :--- | :--- |
| Entrar com o admin do seed | Dashboard com 12 armários |
| Recarregar a página em `/lockers` | Página carrega (sem 404) |
| Reservar para daqui a 30 minutos | Aceita (prova de que o fuso está correto) |
| DevTools → Network na primeira chamada | Pode levar 1–3 s (*cold start*); as seguintes são rápidas |
| Abrir `https://locky-api.vercel.app/docs` | Swagger da API publicada |

---

## Problemas comuns

| Sintoma | Causa provável | Solução |
| :--- | :--- | :--- |
| Build do frontend: "Defina a variável VITE_API_URL" | Variável ausente | Passo 4.3 e *Redeploy* |
| Site mostra "Não foi possível conectar ao servidor" | `VITE_API_URL` errada, ou CORS bloqueando | Console do navegador: se houver erro de CORS, corrija `CORS_ORIGINS` na API |
| API com erro 500 e log `SECRET_KEY padrão não pode ser usada` | `SECRET_KEY` não definida | Passo 1.5 |
| Erro `relation "usuarios" does not exist` | Migrations não rodaram | Passo 3 |
| Workflow: "Segredos não configurados" | Faltam segredos no environment `producao` | Passo 3.2 |
| Login aceita mas telas pedem login de novo | `SECRET_KEY` mudou entre deploys | Use sempre a mesma chave; tokens antigos deixam de valer |

## Limitações conhecidas (documentadas em `debitos-tecnicos.md`)

- **DT-09:** sem limite de tentativas de login; aceitável para demonstração, não para
  uso real.
- **DT-05:** o scheduler não roda no Vercel. A expiração sob demanda garante que
  ninguém veja um armário vencido como reservado, mas reservas vencidas só mudam de
  status quando alguém usa o sistema.
