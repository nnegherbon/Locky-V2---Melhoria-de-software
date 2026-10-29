# Relatório de Manutenção e Melhorias - N2

> Equipe receptora: **[nome da equipe]** · Versão entregue: **v2.0** ·
> Base herdada: tag `1.0.0` + branch `dev` (commit `1fb086d`)

Este documento registra o diagnóstico feito ao receber o Locky, as decisões tomadas e
o motivo de cada uma. A diretriz foi **corrigir e evoluir sem reescrever**: a base
herdada é boa, e os problemas estavam concentrados nas bordas do sistema.

---

## 1. Diagnóstico da recepção

### 1.1. Pontos fortes encontrados (preservados)

- Backend em camadas (`api → services → repositories → models`), com 67 testes,
  **cobertura de 100% exigida no CI**, `ruff` e `mypy --strict` limpos.
- Concorrência de reserva tratada corretamente: `SELECT ... FOR UPDATE` e um índice
  único parcial no banco, validados por um teste com PostgreSQL real.
- Frontend com serviços isolados, paginação, *debounce* e contexto de autenticação.

### 1.2. Problemas encontrados

| ID | Severidade | Problema | Evidência no código herdado |
| :--- | :--- | :--- | :--- |
| P1 | 🔴 Crítica | Não havia como criar usuários: sem endpoint de cadastro e sem seed. Em uma instalação nova, **ninguém conseguia fazer login**. | `backend/app/api/auth.py` só tinha `/login` e `/me` |
| P2 | 🔴 Crítica | A tela de cadastro era simulada e **imprimia a senha no console** do navegador. | `Register.tsx`: `setTimeout` + `console.log({ name, email, password })` |
| P3 | 🔴 Crítica | A administração de armários só alterava o estado do React (tudo sumia ao recarregar). O papel `admin` não era verificado no servidor. | `AdminLockers.tsx` usava `setLockers(...)` e `id: Date.now()` |
| P4 | 🟠 Alta | Sem tratamento de token expirado: após 120 min as telas mostravam erro sem levar ao login. | `services/api.ts` sem interceptor de resposta |
| P5 | 🟠 Alta | A API subia com a `SECRET_KEY` padrão do código, o que permite forjar tokens. A chave padrão tinha 29 bytes, abaixo do recomendado para HS256 (gerava 124 avisos nos testes). | `core/config.py` |
| P6 | 🟡 Média | Documentação contradizia o código: SQLite, `pip install -r pyproject.toml`, rotas `/api/v1/...`, porta 8000, DER com colunas inexistentes. | `README.md`, `docs/handoff.md`, `docs/DER.md` |
| P7 | 🟡 Média | As estatísticas ignoravam armários em manutenção; funções de rótulo duplicadas. | `locker_service.obter_stats`, `AdminLockers.tsx` |
| P8 | 🟡 Média | Reserva futura bloqueia o armário desde a criação; sem limite de antecedência. | `reservation_service.criar_reserva` |
| P9 | 🟡 Média | `datetime.now()` sem fuso: com o servidor em UTC, as regras de horário ficam 3h defasadas para usuários no Brasil. | `schemas/reservation.py`, `reservation_service.py` |

P8 e P9 dependem de decisão de produto ou de migration e foram **registrados como
débito técnico** (ver `debitos-tecnicos.md`) em vez de corrigidos às pressas.

---

## 2. Mudanças realizadas

Cada mudança é um commit separado na branch `feature/n2-manutencao`, seguindo o padrão
do projeto (`ID - descrição`).

### N2-01 · Cadastro real de usuário e seed inicial (corretiva) · P1, P2

| | |
| :--- | :--- |
| **Problema** | O sistema não tinha usuários possíveis; a tela de cadastro vazava a senha. |
| **Solução** | `POST /auth/register`; tela ligada à API com login automático; remoção do `console.log`; script `python -m app.seed`. |
| **Decisões técnicas** | O papel é **sempre `associado`**: aceitá-lo do cliente permitiria que qualquer pessoa virasse admin. O e-mail é normalizado para minúsculas para não permitir `Ana@x.com` e `ana@x.com` como contas distintas. A senha é limitada a 72 caracteres porque o bcrypt ignora o que passa disso. O seed é **idempotente** (pode rodar várias vezes) e lê as credenciais do `.env`. |
| **Benefício** | O projeto funciona do zero; elimina vazamento de credencial. |
| **Arquivos** | `api/auth.py`, `services/auth_service.py`, `schemas/auth.py`, `schemas/user.py`, `seed.py`, `Register.tsx`, `AuthContext.tsx`, `authService.ts` |
| **Testes** | `test_register.py` (11 casos), `test_seed.py` (3 casos) |

### N2-02 · Módulo administrativo real de armários (**evolução**) · P3, P7

| | |
| :--- | :--- |
| **Problema** | A tela existia, mas nada era salvo; a API não tinha autorização por papel. |
| **Solução** | Dependência `require_admin`; `POST /lockers`, `PATCH /lockers/{id}`, `DELETE /lockers/{id}`; tela integrada com paginação, resumo e mensagens de erro. |
| **Regras de negócio** | **RN-A1** número único (409). **RN-A2** o admin só define `disponível` ou `manutenção`; `reservado`/`ocupado` são consequência de reservas, e defini-los à mão dessincronizaria o armário da tabela de reservas. **RN-A3** não se altera o status de armário com reserva ativa (409). **RN-A4** armário com histórico não é excluído (409); a orientação é colocá-lo em manutenção, preservando o histórico dos associados e a integridade referencial. |
| **Decisões técnicas** | Autorização **no servidor**: esconder o menu no frontend não impede uma chamada direta à API. `PATCH` parcial: só os campos enviados mudam. `SELECT ... FOR UPDATE` no armário editado, como no resto do projeto. Corrida de números duplicados é resolvida pelo índice único (`IntegrityError → 409`). |
| **Benefício** | Funcionalidade real, recomendada no handoff da N1, sem migration nova. |
| **Arquivos** | `api/deps.py`, `api/lockers.py`, `services/locker_service.py`, `repositories/*.py`, `schemas/locker.py`, `core/exceptions.py`, `AdminLockers.tsx/.css`, `lockerService.ts`, `types/locker.ts` |
| **Testes** | `test_lockers_admin.py` (22 casos: permissões, regras, corrida, validação) |

### N2-03 · Sessão expirada, chave JWT segura e ajustes (corretiva/preventiva) · P4, P5, P7

| | |
| :--- | :--- |
| **Solução** | Interceptor de 401 que encerra a sessão e mostra "sua sessão expirou" no login; mensagem clara quando a API está fora do ar; `ENV=prod` recusa chave padrão ou menor que 32 bytes; dashboard mostra armários em manutenção. |
| **Decisões técnicas** | O interceptor não age na própria chamada de login (lá o 401 significa senha errada). O AuthContext registra o tratador no `api.ts` para não criar dependência circular. A validação da chave é **fail-fast**: é melhor a API não subir do que subir insegura. |
| **Testes** | `test_config.py` (4 casos) |

### N2-04 · Documentação (corretiva)  · P6

README, DER, handoff e débitos técnicos foram reescritos a partir do código real;
o contrato OpenAPI foi exportado para `docs/api/openapi.json` (importável no Postman).

---

## 3. Classificação das manutenções

| Tipo (ISO/IEC 14764) | Itens |
| :--- | :--- |
| **Corretiva** | N2-01 (cadastro inexistente, senha no console), N2-03 (sessão expirada), N2-04 (docs incorretas) |
| **Evolutiva / Perfectiva** | N2-02 (módulo administrativo) |
| **Preventiva** | N2-03 (chave JWT), dívida registrada DT-06 a DT-11 |
| **Adaptativa** | `ENV` e validação de configuração para ambientes de produção |

---

## 4. Indicadores antes × depois

| Indicador | N1 (herdado) | N2 (entregue) |
| :--- | :--- | :--- |
| Testes automatizados (backend) | 68 | 108 |
| Cobertura de linhas e ramos | 100% | 100% |
| Avisos na suíte de testes | 126 | 2 |
| Endpoints | 9 | 13 |
| Endpoints com autorização por papel | 0 | 3 |
| Telas com dados simulados | 2 (Cadastro, Admin) | 0 |
| Instalação do zero consegue fazer login | Não | Sim (`app.seed`) |

---

## 5. Roteiro de teste manual (QA)

Executar com o banco vazio, após `alembic upgrade head` e `python -m app.seed`.

| # | Passos | Resultado esperado |
| :--- | :--- | :--- |
| 1 | Entrar com `admin@locky.com` / `admin123` | Dashboard com 12 armários, "0 em manutenção" |
| 2 | Cadastrar conta nova em `/register` | Entra direto no dashboard como "Usuário" |
| 3 | Cadastrar de novo com o mesmo e-mail em maiúsculas | Mensagem "Já existe uma conta com este e-mail." |
| 4 | Como associado, abrir `/admin/lockers` pela URL | Redireciona ao dashboard; menu de admin não aparece |
| 5 | Como admin, criar armário `13` e recarregar a página | Armário continua lá |
| 6 | Criar outro armário `13` | Mensagem de número duplicado no modal |
| 7 | Colocar o `13` em manutenção; como associado, tentar reservá-lo | Armário aparece como "Em manutenção" e não pode ser reservado |
| 8 | Associado reserva o `01`; admin tenta "Manutenção" no `01` | Botão desabilitado ("Armário com reserva ativa") |
| 9 | Associado cancela; admin tenta excluir o `01` | Mensagem pedindo para colocar em manutenção (há histórico) |
| 10 | Admin exclui o `13` (nunca reservado) | Some da lista; total volta a 12 |
| 11 | Com `ACCESS_TOKEN_EXPIRE_MINUTES=1`, esperar 1 min e navegar | Volta ao login com "Sua sessão expirou" |
| 12 | Parar a API e tentar navegar | "Não foi possível conectar ao servidor..." |

Os cenários 3 a 10 também foram executados contra a API rodando com PostgreSQL real
durante o desenvolvimento.
