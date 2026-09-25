<!--
## Sync Impact Report

Version change: (template) → 1.0.0
Constituição inicial do projeto Grana.io, criada a partir do constitution-template
(spec-kit 1.0.12) e adaptada do modelo usado no projeto Edge SLM Benchmark Framework.

### Princípios Modificados
- N/A (criação inicial)

### Princípios Adicionados
- I. Localidade e Privacidade dos Dados
- II. Isolamento por Usuário (NÃO NEGOCIÁVEL)
- III. Precisão Monetária e Regras Fiscais como Dados
- IV. Testes Automatizados Obrigatórios no Core (Test-First)
- V. Separação Estrita Backend / Frontend
- VI. Simplicidade e Entrega Incremental

### Seções Adicionadas
- Stack & Technology Constraints
- Development Workflow & Delivery Standards
- Governance

### Seções Removidas
- N/A (criação inicial)

### Templates Verificados
- ✅ .specify/templates/plan-template.md — "Constitution Check" é genérico; os gates são preenchidos
  a partir desta constituição em tempo de /speckit-plan. Sem alteração necessária.
- ✅ .specify/templates/spec-template.md — estrutura de user stories/FRs compatível. Sem alteração.
- ⚠ .specify/templates/tasks-template.md — o template trata testes como OPCIONAIS e sugere
  "commit after each task". Esta constituição prevalece: testes do core são OBRIGATÓRIOS
  (Princípio IV) e os commits seguem os marcos por checkpoint (Development Workflow). O template
  não foi alterado; /speckit-tasks deve aplicar essas regras ao gerar cada tasks.md.

### TODOs Adiados
- Nenhum.

---

Version change: 1.0.0 → 1.1.0
Adiciona referência obrigatória ao documento de arquitetura e padrões de projeto
(`docs/arquitetura.md`). Os padrões ficam no documento, não na constituição, para que ajustes de
arquitetura não exijam emenda; a constituição só torna o documento vinculante.

### Princípios Modificados
- Nenhum.

### Seções Modificadas
- Stack & Technology Constraints — novo item "Arquitetura e padrões de projeto".
- Governance → Revisão de conformidade — o gate "Constitution Check" passa a verificar também a
  aderência a `docs/arquitetura.md`.

### Templates Verificados
- ✅ .specify/templates/plan-template.md — o gate "Constitution Check" já é genérico. Sem alteração.
- ✅ .specify/templates/spec-template.md — sem alteração necessária.
- ✅ .specify/templates/tasks-template.md — sem alteração necessária.

### TODOs Adiados
- Nenhum.
-->

# Grana.io Constitution

## Core Principles

### I. Localidade e Privacidade dos Dados

Todo dado financeiro (gastos, rendas, cenários, usuários) MUST ser armazenado e processado
localmente, no banco PostgreSQL executado via Docker na máquina do usuário. O sistema MUST NOT
enviar dados a serviços externos (APIs de terceiros, analytics, telemetria, CDNs de dados).
Senhas, tokens e segredos MUST NOT aparecer em logs, respostas de erro ou arquivos versionados;
configurações sensíveis MUST vir de variáveis de ambiente (`.env`, nunca versionado, com
`.env.example` versionado).

**Rationale**: Dados financeiros pessoais são sensíveis. A decisão de rodar localmente
(BACKLOG, EP-07) só tem valor se nenhum caminho do sistema vazar esses dados para fora.

### II. Isolamento por Usuário (NÃO NEGOCIÁVEL)

Todo registro de domínio MUST pertencer a exatamente um usuário e MUST herdar da base comum
de "registro com dono". Toda consulta da API MUST ser filtrada pelo usuário autenticado antes
de qualquer outra operação; o dono de um registro MUST ser definido pelo servidor a partir da
sessão, nunca pelo payload do cliente. Tentativas de acessar, alterar ou excluir registro de
outro usuário MUST retornar 404 (não 403), para não revelar a existência do registro. Todo
novo endpoint de domínio MUST ter teste automatizado cobrindo o isolamento.

**Rationale**: O sistema é multiusuário (US-01 a US-03). Um único endpoint sem filtro por dono
expõe as finanças de todos os usuários; por isso a regra é estrutural e testada, não opcional.

### III. Precisão Monetária e Regras Fiscais como Dados

Valores monetários MUST usar `DecimalField` no banco e `Decimal` no Python; o uso de `float`
em qualquer cálculo financeiro é proibido. O arredondamento MUST seguir uma regra única e
documentada (ROUND_HALF_UP, 2 casas decimais) e divisões com resto (ex.: parcelas) MUST
alocar a diferença de centavos de forma determinística, sem sobrar nem faltar dinheiro.
Todo cálculo financeiro (saldo, impostos, projeções) MUST ocorrer no backend, em camada de
serviço isolada das views. Regras fiscais (faixas de INSS, IRRF, deduções) MUST ser dados
versionados por ano de vigência, nunca constantes fixas no código.

**Rationale**: Diferenças de centavos minam a confiança no sistema, e tabelas fiscais mudam
todo ano (US-15). Regras como dados evitam retrabalho e mantêm cálculos antigos reproduzíveis.

### IV. Testes Automatizados Obrigatórios no Core (Test-First)

Todo código do core — models, serviços de cálculo (INSS, IRRF, PJ, saldo, projeções),
endpoints da API, autenticação e isolamento — MUST ter testes automatizados. O ciclo
Red-Green-Refactor MUST ser seguido: testes escritos primeiro, confirmados falhando, e só
então a implementação. Cálculos fiscais MUST ser validados contra casos conferidos
manualmente e documentados no próprio teste. A suíte completa MUST rodar com um único comando
dentro do Docker, e nenhum checkpoint pode ser encerrado com teste falhando. Código de
configuração/glue (ex.: Dockerfile, settings) é isento de testes unitários, mas MUST ser
validado pelo quickstart da feature.

**Rationale**: Um erro silencioso em cálculo de imposto ou saldo leva a decisões financeiras
erradas. Testes primeiro garantem que cada regra do backlog esteja de fato coberta.

### V. Separação Estrita Backend / Frontend

O backend (Django + DRF) e o frontend (React) MUST se comunicar exclusivamente via API REST
com contratos documentados em `specs/<feature>/contracts/`. O frontend MUST NOT conter regra
de negócio nem refazer cálculos financeiros: ele exibe os valores retornados pela API. A URL
da API MUST ser configurável por variável de ambiente. Cada camada MUST poder ser testada
isoladamente.

**Rationale**: Mantém uma única fonte de verdade para os cálculos (Princípio III) e prepara o
sistema para a futura hospedagem em nuvem (RNF-08) sem retrabalho.

### VI. Simplicidade e Entrega Incremental

Cada spec MUST corresponder a um item do BACKLOG (US-xx ou RNF-xx) e entregar algo testável
e demonstrável de forma independente. Abstrações, dependências e generalizações MUST ser
justificadas por necessidade presente, não especulativa (YAGNI). Complexidade adicional MUST
ser registrada na seção "Complexity Tracking" do plan.md, com justificativa. Nenhuma feature
incompleta pode ser mergeada na `main`.

**Rationale**: Projeto de uma pessoa com 6 sprints de 15 dias; complexidade desnecessária
consome o tempo que deveria ir para as funcionalidades do backlog.

## Stack & Technology Constraints

- **Backend**: Python 3.12+, Django 5.2 LTS, Django REST Framework; autenticação por JWT
  (djangorestframework-simplejwt) com login por e-mail.
- **Frontend**: React (Vite), consumindo apenas a API REST do backend.
- **Banco de dados**: PostgreSQL em container Docker com volume persistente local. SQLite é
  permitido apenas para execução rápida de testes fora do Docker.
- **Infraestrutura**: Docker Compose; o sistema inteiro MUST subir com `docker compose up`.
  Hospedagem em nuvem está fora de escopo até a conclusão do backlog (RNF-08, backlog futuro).
- **Testes**: pytest + pytest-django no backend.
- **Localização**: interface em pt-BR; valores em `R$ 1.234,56`; datas em `dd/mm/aaaa`;
  fuso `America/Sao_Paulo`.
- **Dependências novas** MUST ser justificadas no plan.md (Princípio VI).
- **Arquitetura e padrões de projeto**: MUST seguir `docs/arquitetura.md` (camadas, Service
  Layer, Strategy para cálculo por tipo de cenário, padrões de frontend e padrões deliberadamente
  não adotados). Desvios MUST ser registrados em "Complexity Tracking" no plan.md.

## Development Workflow & Delivery Standards

- **Spec-Driven Development**: todo item do backlog MUST passar por
  `/speckit-specify` → (`/speckit-clarify`) → `/speckit-plan` → `/speckit-tasks` →
  (`/speckit-analyze`) → `/speckit-implement`. Nenhum código de aplicação é escrito antes de
  o `tasks.md` da feature ser aprovado pelo responsável.
- **Uma spec por item do backlog**, em `specs/NNN-nome-curto/`, referenciando o ID do BACKLOG
  (ex.: US-01, RNF-01).
- **Marcos de commit**: o `tasks.md` MUST ser organizado em fases que terminam em
  **Checkpoint**, e MUST listar ao final "Commit recomendado após cada checkpoint (Txxx, …)".
  Na implementação, o trabalho MUST parar em cada checkpoint com os testes verdes, apresentar
  o resumo das mudanças e sugerir a mensagem de commit antes de avançar para a próxima fase.
- **Commits e PRs**: são feitos manualmente pelo responsável. Mensagens em pt-BR no padrão
  Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`). Commits e
  PRs MUST NOT conter trailers de coautoria de ferramentas de IA (ex.: `Co-Authored-By`) nem
  rodapés de geração automática.
- **Branches**: uma feature branch por spec (nome igual ao diretório da spec), integrada à
  `main` via Pull Request. A `main` MUST permanecer sempre com a suíte de testes verde.
- **Definition of Done** (por spec): critérios de aceitação do BACKLOG atendidos; testes do
  core escritos e passando; quickstart da feature validado; contratos da API atualizados;
  nenhuma migration pendente; tarefas do `tasks.md` marcadas como concluídas.
- **Demo por sprint**: ao fim de cada sprint MUST haver uma demonstração funcional das
  features entregues no ciclo.

## Governance

Esta constituição prevalece sobre qualquer outra prática, template ou convenção do projeto
(incluindo os templates padrão do spec-kit). Em caso de conflito, vale a constituição.

Alterações requerem:

1. Proposta documentada com justificativa clara (pode ser sugerida pelo assistente de IA).
2. Aprovação explícita do responsável pelo projeto (projeto solo).
3. Registro da nova versão, da data de alteração e do Sync Impact Report neste documento.
4. Plano de migração quando a alteração afetar código já mergeado na `main`.

**Versionamento**: MAJOR para remoção ou redefinição incompatível de princípios; MINOR para
novo princípio ou seção, ou expansão material de orientação; PATCH para clarificações e
correções de redação sem impacto semântico.

**Revisão de conformidade**: todo `plan.md` MUST passar pelo gate "Constitution Check" antes
da pesquisa (Phase 0) e novamente após o design (Phase 1), verificando os princípios desta
constituição e a aderência a `docs/arquitetura.md`. Violações só são aceitas se
registradas em "Complexity Tracking" com justificativa. No início de cada sprint, as features
planejadas MUST ser conferidas contra esta constituição antes da especificação.

**Version**: 1.1.0 | **Ratified**: 2026-09-25 | **Last Amended**: 2026-09-25
