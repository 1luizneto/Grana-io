---

description: "Lista de tarefas da feature 010-gastos-fixos (US-07b)"
---

# Tasks: Gastos Fixos

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/api-fixos.md](contracts/api-fixos.md),
[contracts/tela-fixos.md](contracts/tela-fixos.md), [quickstart.md](quickstart.md)

**Tests**: obrigatórios (Princípio IV), escritos primeiro e confirmados falhando.

**Organization**: um **Checkpoint** por fase (`sh testar.sh` verde, commit e push, sem trailers de
IA). Modo autônomo (`DECISOES-AUTONOMAS.md`).

- **[Story]**: US1 cadastrar (inclui "Repetir todo mês"); US2 gerar ao criar o mês; US3 alterar,
  encerrar, desativar e excluir
- Backend 388, interface 140 hoje.

---

## Phase 1: Setup

- [X] T001 Rodar `sh testar.sh` (388 + 140) como linha de base

  > **Resultado (2026-11-13)**: ✅ 388 + 140 verdes (rodada final da spec 009, mesmo código).
  > Analyze em modo autônomo: nenhum achado crítico; FR-001 a FR-010 com tarefas (FR-009 nas
  > T013 a T017, FR-010 no kit da T004).

**Checkpoint**: o commit leva os artefatos da spec.

---

## Phase 2: Foundational

- [X] T002 Escrever **primeiro** `backend/tests/gastos/test_fixos_models.py` ([data-model.md](data-model.md)): `GastoFixo` herda de `OwnedModel`; campos e tipos (`descricao` 100, `valor` 12/2, `forma_pagamento` com as choices do gasto, `dia_vencimento`, `inicio`, `fim` nulo, `ativo` padrão `True`); `valor` ≤ 0 → `IntegrityError` (`gastos_fixo_valor_positivo`); dia 0 e 32 → `gastos_fixo_dia_valido`; `fim` antes de `inicio` → `gastos_fixo_fim_depois_do_inicio`; categoria com fixo → `RestrictedError`; excluir a conta apaga os fixos; `Gasto.fixo` nulo por padrão e `SET_NULL` ao excluir o fixo; ordem por dia de vencimento e cadastro. Confirmar a **falha**
- [X] T003 Implementar `GastoFixo` e `Gasto.fixo` em `backend/gastos/models.py` e gerar `backend/gastos/migrations/0005_*.py`. Confirmar T002 **verde** e as guardas de isolamento

  > **Resultado (2026-11-13)**: ✅ backend com 402 verdes (388 + 14 do model); interface 140.
  > T002 falhou primeiro (`GastoFixo` inexistente). Migration `gastos.0005_gasto_fixo` aplicada
  > na subida.

**Checkpoint**: tabelas criadas; suítes verdes.

---

## Phase 3: User Story 1 - Cadastrar um gasto fixo (Priority: P1) 🎯 MVP

- [X] T004 [P] [US1] Escrever `backend/tests/gastos/test_fixos_api.py`: `TestIsolamentoFixo(CasosDeIsolamento)` (`montar_payload_criacao` com a categoria da Ana; `payload_alteracao = {"valor": "1600.00"}`); `POST` válido → 201 com exatamente as chaves do [contrato](contracts/api-fixos.md) e `"inicio": "2026-11"`, `"fim": null`, `"ativo": true`; dia 0/32/"x" → "Informe um dia de 1 a 31."; `inicio` "11/2026" e "2026-13" → formato; "1999-12" → ano; `fim` antes do início → mensagem no `fim`; `fim` igual ao início aceito; descrição vazia, valor 0 e categoria da Bia → mensagens da spec 008; `GET` em ordem de dia; sem sessão → 401
- [X] T005 [P] [US1] Acrescentar a `backend/tests/gastos/test_gastos_api.py`: o gasto tem a chave `"fixo"` (`None` por padrão; ajustar `test_lancar`, ponto de atenção 1); `POST` com `"repetir": true` em 10/2026, data 2026-10-10 → 201, `"fixo"` com o id do fixo novo, fixo com dia 10, início "2026-10", mesmos descrição/valor/categoria/forma; `repetir` em mês fechado → 400 de mês fechado e nenhum fixo criado; falha simulada ao criar o fixo → nenhum gasto criado; `PATCH` com `repetir` não cria fixo. Confirmar a **falha** de T004 e T005
- [X] T006 [US1] Implementar `MesAnoField` e `GastoFixoSerializer` em `backend/gastos/serializers.py` ([R-02](research.md), [R-06](research.md)); `GastoSerializer` com `fixo` só leitura e `repetir` só escrita; `GastoFixoViewSet` e a rota `fixos`
- [X] T007 [US1] Criar `backend/gastos/services/fixos.py` com `criar_fixo_do_gasto(gasto)` e usá-lo no `GastoViewSet.perform_create` quando `repetir` (numa transação, [R-04](research.md)). Confirmar T004 e T005 **verdes**

  > **Resultado (2026-11-13)**: ✅ backend com 432 verdes (402 + 30); interface 140.
  > - T004 e T005 falharam primeiro (29 dos 30 casos: rota inexistente, chave `fixo`, `repetir`).
  > - Campos comuns de gasto e fixo numa base (`CamposDeGastoSerializer`), com as mesmas
  >   mensagens; `MesAnoField` para `AAAA-MM`; `dia_vencimento` reaproveita o
  >   `InteiroNaFaixaField` da spec 007.
  > - "Repetir todo mês": gasto e fixo na mesma transação; com falha simulada na criação do fixo,
  >   nenhum dos dois fica.

**Checkpoint**: cadastrar fixos pela API.

---

## Phase 4: User Story 2 - Gerar os fixos ao criar um mês (Priority: P1)

- [X] T008 [P] [US2] Escrever `backend/tests/gastos/test_fixos_service.py` (`gerar_gastos_fixos`): gera um gasto por fixo ativo do período, com descrição, valor, categoria, forma, `fixo` e data do vencimento; dia 31 em novembro → 30; em fevereiro de 2027 → 28 e de 2028 → 29; não gera desativado, antes do início, depois do fim; gera no mês do fim e no do início; não usa fixos de outra conta; mês sem fixos → nada
- [X] T009 [P] [US2] Acrescentar a `backend/tests/gastos/test_meses_api.py`: `POST /api/meses/` gera os gastos fixos (aparecem em `GET /api/gastos/?mes=` e nos totais); falha simulada na geração → 500 sem mês criado (atômico, ponto de atenção 3); criar mês sem fixos continua como na spec 007. Confirmar a **falha**
- [X] T010 [US2] Implementar `gerar_gastos_fixos(mes)` em `backend/gastos/services/fixos.py` e chamá-lo no `MesReferenciaViewSet.perform_create`, dentro da mesma transação ([R-03](research.md)). Confirmar T008 e T009 **verdes**

  > **Resultado (2026-11-13)**: ✅ backend com 444 verdes (432 + 9 do service + 3 da API de
  > meses); interface 140.
  > - T008 e T009 falharam primeiro (`gerar_gastos_fixos` inexistente).
  > - Dia 31: novembro → 30; fevereiro de 2027 → 28; de 2028 → 29 (`calendar.monthrange`).
  > - Mês e gastos na mesma transação: com falha simulada na geração, nenhum mês fica.

**Checkpoint**: meses novos já vêm com os fixos.

---

## Phase 5: User Story 3 - Alterar, encerrar, desativar e excluir (Priority: P2)

- [X] T011 [US3] Acrescentar testes: mudar o valor do fixo não altera gastos já gerados e o mês criado depois usa o valor novo; `PATCH {"ativo": false}` → mês criado depois sem ele; `fim` encerra; `DELETE` do fixo → 204 e os gastos ficam com `"fixo": null`; excluir categoria só com fixos e sem destino → recusa; com destino → fixos movidos ([R-05](research.md)) — em `test_fixos_api.py` e `test_gastos_service.py`. Confirmar a **falha** do caso de categoria
- [X] T012 [US3] Atualizar `excluir_categoria` em `backend/gastos/services/gastos.py`. Confirmar T011 **verde**

  > **Resultado (2026-11-13)**: ✅ backend com 449 verdes (444 + 5); interface 140.
  > - Como previsto, só o caso da categoria falhou primeiro: valor novo só para frente,
  >   desativar, encerrar e excluir mantendo os gastos já valiam pelo desenho (os gastos gerados
  >   são cópias, e a origem é `SET_NULL`).
  > - `excluir_categoria` trata fixos como gastos: exige destino e os move junto.
  > - Os testes ficaram todos em `test_fixos_api.py` (pela API, de ponta a ponta), em vez de
  >   divididos com o `test_gastos_service.py`.

**Checkpoint**: backend completo.

---

## Phase 6: Telas

- [X] T013 [P] Escrever `frontend/src/pages/Fixos/Fixos.test.jsx` ([contrato da tela](contracts/tela-fixos.md)): carregando e vazio; lista com valor em R$, "dia 5", categoria, "desde 11/2026" / "de 11/2026 a 01/2027", "Inativo"; cadastrar (valor "1.500,00" → `"1500.00"`, início padrão = mês de hoje, fim vazio → `null`) com "Gasto fixo cadastrado."; erro de campo ligado ao campo; editar com PATCH e "Gasto fixo atualizado."; desativar/reativar (`{"ativo": false/true}`); excluir com a confirmação do contrato. Atualizar `Layout.test.jsx` (menu com "Gastos fixos" antes de "Categorias")
- [X] T014 [P] Acrescentar a `frontend/src/pages/Mes/Mes.test.jsx`: "Repetir todo mês" envia `"repetir": true` e mostra "Gasto lançado e cadastrado como fixo."; sem marcar, o corpo não tem a chave `repetir`; a caixa não aparece ao editar; gasto com `fixo` mostra a marca "fixo" na tabela. Confirmar a **falha** de T013 e T014
- [X] T015 Criar `frontend/src/api/fixos.js`, `frontend/src/hooks/useFixos.js` e `frontend/src/pages/Fixos/Fixos.jsx` (formulário e lista); rota `/fixos` em `App.jsx`; menu em `Layout.jsx`
- [X] T016 "Repetir todo mês" no `FormularioGasto` e a marca "fixo" na `TabelaGastos`; estilos. Confirmar T013 e T014 **verdes**

  > **Resultado (2026-11-13)**: ✅ interface com 152 verdes (140 + 9 da tela de fixos + 3 da tela
  > do mês); backend 449.
  > - T013 e T014 falharam primeiro (tela inexistente; sem caixa nem marca; menu sem "Gastos
  >   fixos").
  > - Depois de cadastrar, o formulário de fixos volta ao vazio (o primeiro teste pegou que ele
  >   mantinha os valores).
  > - Os campos de mês usam `<input type="month">`, cujo valor já é `AAAA-MM`, o formato da API.

**Checkpoint**: telas prontas.

---

## Phase 7: Polish

- [ ] T017 Validar no navegador o [quickstart.md](quickstart.md) S2 a S6 (inclusive 360 px na tela nova) e limpar
- [ ] T018 [P] README (estado atual, rota `/fixos` e `/api/fixos/`, parágrafo sobre fixos)
- [ ] T019 BACKLOG (US-07b ☑; nota na US-27 sobre recorrentes) e `DECISOES-AUTONOMAS.md`

---

## Dependencies & Execution Order

Setup → Foundational → US1 → US2 → US3 → Telas → Polish. As telas dependem da API (US1 a US3).

**Commit recomendado após cada checkpoint**:

| Checkpoint | Mensagem sugerida |
|---|---|
| T001 | `docs: especifica os gastos fixos (US-07b)` |
| T003 | `feat: adiciona o model de gasto fixo` |
| T007 | `feat: adiciona API de gastos fixos e a opção repetir todo mês (US1)` |
| T010 | `feat: gera os gastos fixos ao criar o mês (US2)` |
| T012 | `feat: leva os gastos fixos junto ao excluir categoria (US3)` |
| T016 | `feat: adiciona a tela de gastos fixos` |
| T019 | `docs: documenta os gastos fixos e conclui US-07b` |
