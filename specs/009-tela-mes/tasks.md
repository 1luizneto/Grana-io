---

description: "Lista de tarefas da feature 009-tela-mes (US-27)"
---

# Tasks: Tela do Mês

**Input**: documentos de design em `/specs/009-tela-mes/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[contracts/tela-mes.md](contracts/tela-mes.md), [quickstart.md](quickstart.md)

**Tests**: **obrigatórios** (Princípio IV): formatação e lógica das telas (Vitest + Testing
Library, padrão da spec 005). Testes primeiro, confirmando a falha.

**Organization**: um **Checkpoint** por fase, com `sh testar.sh` verde, commit e push (sem trailers
de IA). Modo autônomo (decisões em `DECISOES-AUTONOMAS.md`).

## Format: `[ID] [P?] [Story] Description`

- **[Story]**: US1 escolher e criar mês; US2 lançar e totais; US3 corrigir e excluir; US4 filtrar e
  ordenar; US5 fechar, reabrir e excluir mês; US6 excluir categoria com destino
- Backend 387, interface 85 hoje. Testes do frontend: `docker compose run --rm frontend npm test`.

---

## Phase 1: Setup

- [X] T001 Rodar `sh testar.sh` (387 + 85) como linha de base

  > **Resultado (2026-11-13)**: ✅ 387 + 85 verdes. Analyze em modo autônomo: nenhum achado
  > crítico; todas as FR têm tarefa (FR-001/002/003/004 na US1, FR-005/006/007/008/011 na US2 a
  > US4, FR-009/010 na US3 e US5, FR-012 na US6, FR-013 no Polish e nos testes de rótulos).

**Checkpoint**: o commit leva os artefatos da spec.

---

## Phase 2: Foundational

**Purpose**: formatação, módulos de API, hooks e o aviso de sucesso.

- [X] T002 [P] Escrever **primeiro** `frontend/src/utils/formatacao.test.js` ([R-03](research.md)): `formatarMoeda` ("0.00" → "R$ 0,00", "150.30" → "R$ 150,30", "1234.50" → "R$ 1.234,50", "9999999999.99" → "R$ 9.999.999.999,99", "-5.00" → "-R$ 5,00"); `formatarData("2026-10-05")` → "05/10/2026"; `paraValorDaApi` ("1.234,56" → "1234.56", "12,5" → "12.5", "12.50" → "12.50", " 7 " → "7", "" → ""); `emCentavos("150.30")` → `15030n`, `emCentavos("0.05")` → `5n`. Confirmar a **falha**
- [X] T003 Implementar `frontend/src/utils/formatacao.js` sem `Number`/`parseFloat`. Confirmar T002 **verde**
- [X] T004 [P] Criar `frontend/src/api/meses.js` e `frontend/src/api/gastos.js` ([R-02](research.md)) e mudar `excluirCategoria(id, moverPara)` em `frontend/src/api/categorias.js` (acrescenta `?mover_para=` quando informado)
- [X] T005 [P] Em `frontend/src/components/AvisoFormulario.jsx`, `tipo="sucesso"` com `role="status"` e classe `aviso-sucesso` ([R-07](research.md))
- [X] T006 Criar `frontend/src/hooks/useMeses.js` e `frontend/src/hooks/useGastosDoMes.js` no padrão do `useCategorias` (estado `carregando`/`erroCarregar`, ações devolvendo `{ok}`/`{ok:false, erro}` e recarregando)

  > **Resultado (2026-11-13)**: ✅ interface com 102 verdes (85 + 17 de formatação); backend 387.
  > - T002 falhou primeiro (módulo inexistente).
  > - `formatacao.js` só manipula texto (e `BigInt` para ordenar); acrescentei `paraValorDigitado`
  >   ("1234.56" → "1234,56"), usado na edição.
  > - Hooks sem teste próprio: são cobertos pelos testes de página das fases seguintes, como o
  >   `useCategorias` na spec 006.

**Checkpoint**: base pronta; suítes verdes.

---

## Phase 3: User Story 1 - Escolher e criar o mês (Priority: P1) 🎯 MVP

**Independent Test**: quickstart S2.

- [X] T007 [US1] Escrever `frontend/src/pages/Mes/Mes.test.jsx` (com `renderizarComRotas` nas rotas `/meses` e `/meses/:id`, `simularApi` e data fixada, ponto de atenção 3): `/meses` com o mês de hoje na lista → vai para `/meses/<id dele>`; sem o de hoje → vai para o último; sem meses → "Nenhum mês criado. Crie o primeiro abaixo."; `/meses/999` → "Mês não encontrado."; trocar no `select` "Mês" → endereço muda; criar mês (Novo mês: Novembro, 2026) → `POST /meses/` com `{"mes": 11, "ano": 2026}`, "Mês criado." e endereço do mês novo; padrão do formulário = mês seguinte ao último; mês repetido → "Este mês já foi criado."; fechados aparecem com " (fechado)". Atualizar `frontend/src/components/Layout.test.jsx`: menu com "Gastos do mês" (`/meses`) entre "Início" e "Categorias". Confirmar a **falha**
- [X] T008 [US1] Criar `frontend/src/components/SeletorMes.jsx` ([R-06](research.md)) e `frontend/src/pages/Mes/Mes.jsx` com a escolha do mês inicial ([R-01](research.md)), o cabeçalho do mês e o estado vazio; rotas em `frontend/src/App.jsx`; menu em `frontend/src/components/Layout.jsx`. Confirmar T007 **verde**

  > **Resultado (2026-11-13)**: ✅ interface com 111 verdes (102 + 9 da tela + menu atualizado);
  > backend 387.
  > - T007 falhou primeiro (página inexistente; menu sem "Gastos do mês").
  > - O seletor do topo ficou com o rótulo **"Escolher mês"** (o formulário "Novo mês" já tem um
  >   campo "Mês"); contrato ajustado.
  > - Componente novo `CampoSelecao` (como o `CampoTexto`, para `select`), usado também no
  >   formulário de gasto.
  > - Nos testes, a mensagem de sucesso é buscada pelo texto: o `<output>` do auxiliar de rotas
  >   também tem papel "status".

**Checkpoint**: escolher e criar meses pela tela.

---

## Phase 4: User Story 2 - Lançar gastos e ver os totais (Priority: P1)

**Independent Test**: quickstart S3.

- [X] T009 [US2] Acrescentar a `Mes.test.jsx`: totais exibidos como a API mandou ("Total do mês" "R$ 223,45"; "Alimentação" "R$ 200,00" "2 gastos"; "1 gasto"); mês sem gastos → "Nenhum gasto neste mês." e "R$ 0,00"; tabela com data DD/MM/AAAA, descrição, categoria, forma pelo nome (ou "—") e valor em R$; lançar "Mercado", "1.234,56", data, Alimentação, Pix → `POST /gastos/` com `{"descricao": "Mercado", "valor": "1234.56", "data": ..., "mes": <id>, "categoria": <id>, "forma_pagamento": "pix"}`, "Gasto lançado.", recarga de gastos e totais, descrição e valor limpos, data e categoria mantidas, foco na descrição; botão "Lançando…" desabilitado durante o envio; erro 400 de campo → mensagem ligada ao campo (`aria-describedby`) e valores mantidos; 400 `detail` → alerta geral; data padrão = hoje dentro do mês, senão dia 1. Confirmar a **falha**
- [X] T010 [US2] Criar `frontend/src/components/TotaisMes.jsx`, `frontend/src/components/FormularioGasto.jsx` (modo criar) e `frontend/src/components/TabelaGastos.jsx` (só a tabela) e ligá-los em `Mes.jsx` com o `useGastosDoMes` e o `useCategorias`. Confirmar T009 **verde**

  > **Resultado (2026-11-13)**: ✅ interface com 119 verdes (111 + 8); backend 387.
  > - T009 falhou primeiro em 8 casos (sem totais, tabela e formulário).
  > - `CampoTexto` passou a aceitar `ref` (React 19) e atributos extras (`min`, `max`,
  >   `placeholder`, `inputMode`), para devolver o foco à descrição e limitar a data ao mês.
  > - O formulário já nasce preparado para o modo editar (US3): a página o remonta com `key`.

**Checkpoint**: lançar e ver totais pela tela.

---

## Phase 5: User Story 3 - Corrigir e excluir gastos (Priority: P2)

**Independent Test**: quickstart S4.

- [ ] T011 [US3] Acrescentar a `Mes.test.jsx`: "Editar Mercado" carrega o formulário ("Editar gasto", valor "150,30") → salvar faz `PATCH /gastos/<id>/` com os campos e mostra "Gasto atualizado."; "Cancelar edição" volta ao modo lançar sem chamar a API; "Excluir Mercado" pergunta `Excluir o gasto "Mercado" de R$ 150,30?`; `false` não chama a API; `true` faz `DELETE` e mostra "Gasto excluído."; erro de exclusão vira alerta. Confirmar a **falha**
- [ ] T012 [US3] Modo editar no `FormularioGasto` (valor da API mostrado com vírgula) e ações na `TabelaGastos`; confirmação com `window.confirm`. Confirmar T011 **verde**

**Checkpoint**: corrigir e excluir pela tela.

---

## Phase 6: User Story 4 - Filtrar e ordenar (Priority: P2)

**Independent Test**: quickstart S5.

- [ ] T013 [US4] Acrescentar a `Mes.test.jsx`: filtro "Categoria" com "Todas as categorias" + categorias; escolher Transporte mostra só os dele; filtro sem gastos → "Nenhum gasto nesta categoria."; "Ordenar por": "Maior valor" (inclusive "1234.56" antes de "999.99" e empate mantendo a ordem da API), "Menor valor", "Data (mais recente)" (inverte a da API). Confirmar a **falha**
- [ ] T014 [US4] Filtro e ordenação na `TabelaGastos` ([R-04](research.md)), com `emCentavos`. Confirmar T013 **verde**

**Checkpoint**: filtrar e ordenar.

---

## Phase 7: User Story 5 - Fechar, reabrir e excluir o mês (Priority: P2)

**Independent Test**: quickstart S6.

- [ ] T015 [US5] Acrescentar a `Mes.test.jsx`: "Fechar mês" → `PATCH /meses/<id>/` `{"fechado": true}`, "Mês fechado.", aviso de mês fechado, formulário desabilitado e sem "Editar"/"Excluir" nas linhas, situação "Fechado"; "Reabrir mês" → `{"fechado": false}` e "Mês reaberto."; "Excluir mês" pergunta `Excluir o mês 11/2026?`; confirmando → `DELETE`, "Mês excluído." e volta a `/meses` (escolhe outro); erro (mês com gastos) → alerta com a mensagem da API. Confirmar a **falha**
- [ ] T016 [US5] Ações do mês em `Mes.jsx` (com o `useMeses`) e `desabilitado` no formulário e na tabela. Confirmar T015 **verde**

**Checkpoint**: ciclo do mês pela tela.

---

## Phase 8: User Story 6 - Excluir categoria com destino (Priority: P2)

**Independent Test**: quickstart S7.

- [ ] T017 [US6] Em `frontend/src/pages/Categorias/Categorias.test.jsx`, trocar os testes de exclusão por painel ([R-09](research.md)): "Excluir Saúde" mostra `Excluir a categoria "Saúde"?`, `select` "Mover os gastos para" sem a própria e com "Outros" escolhida quando existir; "Cancelar" fecha sem chamar a API; "Excluir" faz `DELETE /categorias/<id>/?mover_para=<outros>` e recarrega; sem outra categoria → "Não há outra categoria para receber gastos." e `DELETE` sem parâmetro; erro da API → alerta. Confirmar a **falha**
- [ ] T018 [US6] Painel de exclusão em `frontend/src/pages/Categorias/Categorias.jsx` e `excluir(id, moverPara)` no `useCategorias`. Confirmar T017 **verde**

**Checkpoint**: categorias com gastos excluíveis pela tela.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T019 [P] Estilos em `frontend/src/estilos.css` (seletor, cabeçalho do mês, totais, formulário em grade, tabela e cartões abaixo de 640 px, aviso de sucesso) e link "Gastos do mês" no `frontend/src/pages/Inicio/Inicio.jsx`
- [ ] T020 Validar no navegador o [quickstart.md](quickstart.md) S2 a S8 (com o tempo do SC-001 e 360 px) e limpar (S9)
- [ ] T021 [P] Atualizar o `README.md` (estado atual; rota `/meses` da interface)
- [ ] T022 Fechar a Definition of Done: suítes verdes, tarefas marcadas; `BACKLOG.md` (US-27: critérios atendidos ☑, recorrentes/parcelados anotados; US-08 "confirmação antes de excluir" ☑; RNF-03 3º critério ☑; US-05 nota da tela); `DECISOES-AUTONOMAS.md`

**Checkpoint**: feature pronta para PR (depois da 008).

---

## Dependencies & Execution Order

```text
Setup → Foundational → US1 → US2 → US3 → US4 → US5 → US6 → Polish
```

`Mes.jsx` e `Mes.test.jsx` são editados por US1 a US5, em sequência. US6 só depende da Foundational
(T004) e pode ir em paralelo às US2 a US5.

## Implementation Strategy

MVP: Setup + Foundational + US1 + US2 (escolher o mês, lançar e ver os totais).

**Commit recomendado após cada checkpoint**:

| Checkpoint | Mensagem sugerida |
|---|---|
| T001 | `docs: especifica a tela do mês (US-27)` |
| T006 | `feat: adiciona formatação, API e hooks de meses e gastos na interface` |
| T008 | `feat: adiciona seletor e criação de mês na interface (US1)` |
| T010 | `feat: permite lançar gastos e ver os totais na tela do mês (US2)` |
| T012 | `feat: permite corrigir e excluir gastos na tela do mês (US3)` |
| T014 | `feat: adiciona filtro e ordenação de gastos (US4)` |
| T016 | `feat: permite fechar, reabrir e excluir o mês pela tela (US5)` |
| T018 | `feat: pergunta o destino dos gastos ao excluir categoria (US6)` |
| T022 | `docs: documenta a tela do mês e conclui US-27` |
