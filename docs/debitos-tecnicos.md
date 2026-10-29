# Registro e Gestão de Débito Técnico - Locky

## 1. Política de Gestão de Débito Técnico

Na engenharia do **Locky**, reconhecemos que o débito técnico é uma consequência inevitável da evolução rápida de software. Contudo, para manter a sustentabilidade da arquitetura e evitar o envenenamento da base de código, adotamos a política de **Registro Obrigatório e Alocação Contínua de Pagamento**.

### 1.1. Regra de Registro
Todo atalho técnico, decisão temporária de projeto, falta de cobertura de testes ou dependência defasada assumida pela equipe **deve ser registrado formalmente** no backlog do projeto.

Cada registro deve conter:
- **Título**: Descrição objetiva do débito.
- **Contexto**: Motivo pelo qual o atalho foi adotado e quando ocorreu.
- **Impacto**: Consequências da não resolução (segurança, performance, manutenibilidade).
- **Esforço estimado**: Classificação em P (Pequeno), M (Médio) ou G (Grande).
- **Label**: Tag `debito-tecnico` no GitHub Issues / Jira.

### 1.2. Alocação de Esforço (Orçamento de 15%)
A equipe reserva **15% do esforço de desenvolvimento de cada sprint/ciclo** exclusivamente para a refatoração e quitação dos débitos técnicos registrados de maior prioridade.

---

## 2. Matriz de Priorização de Débitos

| Prioridade | Categoria | Critério de Classificação | Prazo Máximo de Resolução |
| :--- | :--- | :--- | :--- |
| 🔴 **Crítica** | Segurança / Concorrência | Riscos de vazamento de dados, falhas de autenticação ou corrupção de estado no BD. | Próximo ciclo imediato. |
| 🟠 **Alta** | Performance / Infraestrutura | Degradação perceptível no tempo de resposta da API ou gargalos de banco de dados. | Em até 2 ciclos. |
| 🟡 **Média** | Manutenibilidade | Código duplicado, acoplamento excessivo ou abstrações incompletas. | Conforme orçamento de 15%. |
| 🟢 **Baixa** | Qualidade Interna | Legibilidade, documentação interna de funções ou formatação de código. | Backlog geral. |

---

## 3. Inventário de Débitos Técnicos Identificados (N1)

| ID | Título do Débito | Contexto | Impacto | Prioridade | Esforço |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DT-01** | **Substituição do SQLite por PostgreSQL em produção** | O banco SQLite foi utilizado para agilizar a entrega inicial e a esteira local. | SQLite não oferece controle nativo de concorrência com alto volume de gravações concorrentes. | 🟠 Alta | M |
| **DT-02** | **Mecanismo de Refresh Token / Expiração de Sessão** | A autenticação atual utiliza apenas tokens JWT de curta duração armazenados em `localStorage`. | Sem o refresh token, o usuário é deslogado abruptamente quando o JWT expira sem renovação silenciosa. | 🟡 Média | M |
| **DT-03** | **Notificação ativa de expiração via Email/Push** | A expiração de armário é tratada no banco via scheduler, mas não envia avisos prévios ao aluno. | O aluno pode perder a hora do fim da reserva sem aviso prévio. | 🟡 Média | G |
| **DT-04** | **Testes End-to-End (E2E) com Playwright/Cypress** | Atualmente temos testes unitários e de integração no backend, mas o frontend possui apenas testes manuais de QA. | Mudanças na API podem quebrar fluxos do frontend sem detecção prévia no CI. | 🟡 Média | G |
| **DT-05** | **Isolamento de Scheduler em Worker Dedicado** | O scheduler de expiração de reservas roda na mesma thread da aplicação FastAPI (`APScheduler`). | Em cenários de alta carga na API, o scheduler pode ter atrasos na execução de varreduras. | 🟢 Baixa | M |

### 3.1. Situação dos débitos da N1 após a recepção (N2)

| ID | Situação na N2 | Observação |
| :--- | :--- | :--- |
| DT-01 | ✅ **Já estava resolvido** | O código da N1 já usa PostgreSQL (`docker-compose.yml`, CI). O que estava errado era a documentação, corrigida na N2. SQLite é usado apenas nos testes em memória. |
| DT-02 | 🟡 **Parcialmente tratado** | A N2 trata o token expirado (interceptor de 401 + aviso no login). A renovação silenciosa (refresh token) continua pendente. |
| DT-03 | ⏳ Pendente | Sem alteração. |
| DT-04 | ⏳ Pendente | Sem alteração. A N2 incluiu um roteiro de teste manual em `melhorias-n2.md`. |
| DT-05 | ⏳ Pendente | Sem alteração. Atenção: com mais de um worker do Uvicorn, cada processo sobe seu próprio scheduler. |

### 3.2. Novos débitos identificados na N2

| ID | Título do Débito | Contexto | Impacto | Prioridade | Esforço |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DT-06** | **Reserva futura bloqueia o armário imediatamente / status `OCUPADO` sem uso** | `criar_reserva` muda o armário para `RESERVADO` na criação, e não há limite de antecedência. Não existe check-in, então `OCUPADO` nunca é atribuído. | Uma reserva para daqui a uma semana prende o armário a semana toda. Depende de decisão do PO (RN03 pendente desde a N1). | 🟠 Alta | M |
| **DT-07** | **Datas e horas sem fuso horário** | `datetime.now()` e colunas `Date`/`Time` sem timezone. | Com o servidor em UTC, validação de "data no passado" e expiração ficam 3h defasadas para usuários no Brasil. | 🟠 Alta | M |
| **DT-08** | **Formato de erro diferente do contrato** | A API retorna `{ "detail": "..." }`; o contrato propunha `{ "error": { "code", "message" } }`. | O frontend depende do texto da mensagem, que pode mudar. | 🟡 Média | M |
| **DT-09** | **Sem limite de tentativas de login** | `/auth/login` e `/auth/register` aceitam requisições ilimitadas. | Permite ataques de força bruta a senhas. | 🔴 Crítica (em produção) | P |
| **DT-10** | **Expiração usa o mesmo status de conclusão** | O scheduler marca reservas vencidas como `CONCLUIDA`. | Não é possível diferenciar uma reserva usada de uma que venceu (o DER da N1 citava `EXPIRADA`). Exige migration do enum. | 🟢 Baixa | P |
| **DT-11** | **Promoção de usuário a admin só pelo seed** | Não há tela/endpoint para conceder o papel `admin`. | Criar um segundo admin exige acesso ao banco. | 🟢 Baixa | P |

---

## 4. Fluxo de Quitação de Débito Técnico

1. **Triagem no Início do Ciclo**: Durante o planejamento do ciclo, o Product Owner (PO) e o Time de Desenvolvimento selecionam débitos que se enquadrem no orçamento de 15%.
2. **Criação de Branch**: Criar branch com o prefixo `refactor/DT-XX-descricao`.
3. **Validação por Testes**: Nenhuma refatoração de débito técnico pode alterar o comportamento esperado das APIs existentes. Suíte de testes automatizados deve passar sem regressões.
4. **Fechamento**: Encerrar a issue associada e contabilizar o débito quitado no histórico da release.
