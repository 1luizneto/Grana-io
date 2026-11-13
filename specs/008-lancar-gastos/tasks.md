---

description: "Lista de tarefas da feature 008-lancar-gastos (US-07 + US-08)"
---

# Tasks: Lançar, Editar e Excluir Gastos

**Input**: documentos de design em `/specs/008-lancar-gastos/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/api-gastos.md](contracts/api-gastos.md),
[quickstart.md](quickstart.md)

**Tests**: **obrigatórios** (Princípio IV): dinheiro, model, service e API, com o kit de
isolamento. Testes primeiro, confirmando a falha; se algum passar de primeira, registrar e provar a
falha de outro jeito.

**Organization**: cada fase termina num **Checkpoint**: suítes verdes (`sh testar.sh`), resumo,
commit com a mensagem sugerida e push, sem trailers de IA. PR e merge ficam com o responsável.
Executado em **modo autônomo** (decisões em `DECISOES-AUTONOMAS.md`).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: US1 lançar; US2 lista e totais; US3 corrigir e excluir; US4 proteger o histórico
- Backend: `docker compose run --rm backend pytest` (276 hoje). Interface: 85, sem mudança.

---

## Phase 1: Setup

- [X] T001 Subir o sistema e rodar `sh testar.sh` (276 + 85) e `makemigrations --check --dry-run`

  > **Resultado (2026-11-13)**: ✅ 276 + 85 verdes; `makemigrations --check` sem alterações.
  > Analyze feito em modo autônomo: nenhum achado crítico. FR-002 e FR-003 estão cobertos pela
  > faixa "FR-001 a FR-004" da US1, e o FR-012 pelo kit de isolamento; o `payload_criacao` do kit
  > só é usado num teste, então o gancho do R-09 não afeta as subclasses existentes.

**Checkpoint**: linha de base; o commit leva os artefatos da spec (`specs/008-lancar-gastos/`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: regra de dinheiro, model `Gasto` e o gancho do kit de isolamento.

- [X] T002 [P] Escrever **primeiro** `backend/tests/core/test_dinheiro.py` ([research R-02](research.md)): `CENTAVO == Decimal("0.01")`; `arredondar(Decimal("2.345")) == Decimal("2.35")` e `arredondar(Decimal("2.344")) == Decimal("2.34")` (ROUND_HALF_UP); `arredondar(Decimal("-2.345")) == Decimal("-2.35")`; `arredondar(Decimal("5")) == Decimal("5.00")` com expoente de 2 casas; `arredondar(0)` aceita inteiro.
- [X] T003 [P] Escrever **primeiro** `backend/tests/gastos/test_gastos_models.py` ([data-model.md](data-model.md)):
  - `Gasto` herda de `OwnedModel`; `descricao` é `CharField(max_length=100)`; `valor` é `DecimalField(max_digits=12, decimal_places=2)`; `forma_pagamento` é `CharField(max_length=10)` com `choices` = `FORMAS_PAGAMENTO` (`dinheiro`, `debito`, `credito`, `pix`), `blank=True`, `default=""`;
  - `valor` 0 e negativo → `IntegrityError` pela `gastos_gasto_valor_positivo`;
  - excluir mês ou categoria com gasto → `RestrictedError`, e nada é apagado;
  - excluir o **usuário** apaga categorias, meses e gastos dele sem erro, e não toca nos da outra conta (ponto de atenção 1);
  - `Gasto.objects.do_dono(u)` em ordem de `data` e, na mesma data, de `id`;
  - `str(gasto)` devolve a descrição.

  Rodar e confirmar a **falha**.
- [X] T004 Implementar `backend/core/dinheiro.py`: `CENTAVO`, `arredondar(valor)` (`Decimal(valor).quantize(CENTAVO, ROUND_HALF_UP)`), com docstring citando o Princípio III. Confirmar T002 **verde**
- [X] T005 Implementar em `backend/gastos/models.py` `FORMAS_PAGAMENTO` e `Gasto(OwnedModel)` conforme o [data-model](data-model.md) (`mes` e `categoria` com `on_delete=models.RESTRICT, related_name="gastos"`; `ordering = ["data", "id"]`; `CheckConstraint(condition=Q(valor__gt=0), name="gastos_gasto_valor_positivo")`). Gerar `backend/gastos/migrations/0004_gasto.py`. Confirmar T003 **verde** e as guardas de isolamento
- [X] T006 Em `backend/tests/isolamento.py`, acrescentar o gancho `montar_payload_criacao(self, usuario)` que devolve `self.payload_criacao`, usado por `test_dono_do_payload_ignorado_na_criacao` ([research R-09](research.md)); atualizar a docstring. Confirmar as subclasses existentes verdes

  > **Resultado (2026-11-13)**: ✅ backend com 290 verdes (276 + 5 de dinheiro + 9 do model);
  > interface 85.
  > - T002 e T003 falharam primeiro (`core.dinheiro` e `Gasto` inexistentes).
  > - Ponto de atenção 1 confirmado: com `RESTRICT`, excluir mês ou categoria com gasto lança
  >   `RestrictedError`, e excluir a conta apaga categorias, meses e gastos dela sem erro (os da
  >   Bia ficam).
  > - `gastos.0004_gasto` aplicada na subida; `makemigrations --check` sem pendências.
  > - T006: gancho `montar_payload_criacao(usuario)` no kit; as 4 subclasses existentes verdes.

**Checkpoint**: tabela `gastos_gasto` criada; suítes verdes.

---

## Phase 3: User Story 1 - Lançar um gasto (Priority: P1) 🎯 MVP

**Goal**: `POST /api/gastos/` com todas as validações e o bloqueio de mês fechado (FR-001 a FR-004,
FR-008 na criação, FR-011 a FR-013).

**Independent Test**: quickstart S2; kit de isolamento verde.

### Tests for User Story 1 ⚠️

- [X] T007 [P] [US1] Escrever `backend/tests/gastos/test_gastos_service.py` (parte de mês fechado): `exigir_mes_aberto(aberto)` não lança; com um mês fechado 10/2026 lança `RegraViolada` com a mensagem "O mês 10/2026 está fechado. Reabra o mês para alterar os gastos."; com vários meses, acusa o primeiro fechado; `None` é ignorado.
- [X] T008 [P] [US1] Escrever `backend/tests/gastos/test_gastos_api.py` com:
  - `TestIsolamentoGasto(CasosDeIsolamento)`: `modelo = Gasto`, `url_lista = "/api/gastos/"`, `payload_alteracao = {"descricao": "Feira"}`, `criar(usuario)` com mês 10/2026 e categoria "Alimentação" do `usuario` (`get_or_create`) e `montar_payload_criacao(usuario)` com os ids do mês e da categoria da Ana;
  - `POST` válido → 201 com exatamente `{"id", "descricao", "valor", "data", "forma_pagamento", "mes", "categoria"}`, `"valor": "150.30"`;
  - valor numérico em JSON (`150.3`) → `"150.30"`; `forma_pagamento` ausente, `""` e `null` → `""`; `"cheque"` → mensagem de forma de pagamento;
  - descrição com espaços nas pontas é aparada; vazia ou só espaços → obrigatório; 101 caracteres → mensagem de limite;
  - valor: `"abc"` e `"12,50"` → numérico; `0` e `-5` → maior que zero; `"10.555"` → 2 casas; `"10000000000.00"` → limite; ausente → obrigatório (ponto de atenção 2: conferir as chaves de erro do DRF);
  - data: `"2026-13-01"` e `"ontem"` → data válida; `"2026-11-05"` em 10/2026 → "A data precisa estar dentro de 10/2026."; `"2026-10-31"` aceita;
  - mês e categoria da Bia → "Registro não encontrado." em cada campo;
  - mês fechado → `400 {"detail": "O mês 10/2026 está fechado. Reabra o mês para alterar os gastos."}` e nada criado;
  - `GET /api/gastos/formas-pagamento/` → as 4 formas na ordem do [R-08](research.md); sem sessão → 401.

  Rodar e confirmar a **falha**.

### Implementation for User Story 1

- [X] T009 [US1] Criar `backend/gastos/services/gastos.py` com `RegraViolada(Exception)` e `exigir_mes_aberto(*meses)` ([research R-03](research.md)). Confirmar T007 **verde**
- [X] T010 [US1] Implementar `GastoSerializer(RegistroComDonoSerializer)` em `backend/gastos/serializers.py`: `fields = ["id", "descricao", "valor", "data", "forma_pagamento", "mes", "categoria", "dono"]`; `descricao` com obrigatório em `blank`; `valor = DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))` com as mensagens do [R-02](research.md); `data` com a mensagem de data inválida; `forma_pagamento` opcional aceitando `null` como `""`, com a mensagem do R-08; `mes` e `categoria` com `RelacionadoDoDonoField`; `validate` confere a data contra o mês (o enviado ou o atual, ponto de atenção 3) com `{"data": ["A data precisa estar dentro de MM/AAAA."]}`
- [X] T011 [US1] Implementar `GastoViewSet(FiltroPorDonoMixin, ModelViewSet)` em `backend/gastos/views.py` (`queryset` com `select_related("mes", "categoria")`), com `perform_create` chamando `exigir_mes_aberto` e um tradutor de `RegraViolada` para `ValidationError({"detail": ...})`; ação `formas-pagamento` (`url_path="formas-pagamento"`); registrar `gastos` em `backend/gastos/urls.py`. Confirmar T008 **verde** e as guardas de rotas das specs 003 e 004
- [X] T012 [US1] Validar o S2 do [quickstart.md](quickstart.md) com `curl` e limpar

  > **Resultado (2026-11-13)**: ✅ backend com 339 verdes (290 + 4 do service + 8 do kit + 37 da
  > API); interface 85.
  > - T007 e T008 falharam primeiro (`gastos.services.gastos` inexistente).
  > - Ponto de atenção 2 confirmado: o DRF 3.18 usa as chaves `invalid` (inclusive para `"12,50"`
  >   e `"NaN"`), `min_value`, `max_decimal_places` e `max_digits` (13 dígitos cai em
  >   `max_digits` antes de `max_whole_digits`). Texto vazio cairia em `invalid`; o `ValorField`
  >   o trata como ausente, como o `InteiroNaFaixaField` da spec 007.
  > - Regra de mês fechado no service (`exigir_mes_aberto`), chamada no `perform_create`; o
  >   gerenciador `regras_como_erro_400` traduz `RegraViolada` para `400 {"detail"}`.
  > - S2 com `curl`: 201 `"valor": "150.30"`; 400 maior que zero; 400 data fora de 10/2026; 400
  >   duas casas. Gasto e mês de teste excluídos.

**Checkpoint**: lançar gastos pela API; suítes verdes.

---

## Phase 4: User Story 2 - Ver os gastos e os totais do mês (Priority: P1)

**Goal**: lista filtrada e totais exatos (FR-005, FR-006).

**Independent Test**: quickstart S3.

### Tests for User Story 2 ⚠️

- [X] T013 [P] [US2] Acrescentar a `backend/tests/gastos/test_gastos_service.py`: `totais_do_mes(mes)` com 0.10 + 0.20 → total `Decimal("0.30")` (SC-003); Mercado 150.30 + Feira 49.70 (Alimentação) e Uber 23.45 (Transporte) → total 223.45, Alimentação 200.00 (2 gastos) antes de Transporte 23.45 (1); empate de total em ordem alfabética; gastos de outro mês e de outra conta não entram; mês sem gastos → total 0.00 e lista vazia; todos os totais com 2 casas.
- [X] T014 [P] [US2] Acrescentar a `backend/tests/gastos/test_gastos_api.py`: `GET ?mes=` traz só os do mês, por data e lançamento; `?categoria=` filtra; os dois juntos; `?mes=abc` → `400 {"mes": ["Informe o número do mês."]}`; `?categoria=abc` → mensagem da categoria; `?mes=<id da Bia>` → `[]`; `GET /api/meses/{id}/totais/` no formato do [contrato](contracts/api-gastos.md), com valores em texto; totais de mês da Bia → 404; totais refletem lançamento, alteração e exclusão.

  Rodar e confirmar a **falha**.

### Implementation for User Story 2

- [X] T015 [US2] Implementar `totais_do_mes(mes)` em `backend/gastos/services/gastos.py`: `Sum("valor")` por categoria (com nome, cor e quantidade), total geral, `arredondar` na saída, ordem por total decrescente e nome (`ORDEM_ALFABETICA` das categorias). Devolver estruturas Python (dataclasses `TotaisDoMes` e `TotalDaCategoria`). Confirmar T013 **verde**
- [X] T016 [US2] Em `GastoViewSet.get_queryset`, filtros `mes` e `categoria` ([R-05](research.md)); em `MesReferenciaViewSet`, `@action(detail=True) totais` com um serializer de saída (`TotaisDoMesSerializer`, valores com `DecimalField`). Confirmar T014 **verde**
- [X] T017 [US2] Validar o S3 do [quickstart.md](quickstart.md) com `curl` e limpar

  > **Resultado (2026-11-13)**: ✅ backend com 354 verdes (339 + 6 do service + 9 da API);
  > interface 85.
  > - T013 e T014 falharam primeiro (`totais_do_mes` inexistente).
  > - Totais com `values().annotate(Sum, Count)` agrupados por categoria e ordem
  >   `-total` + nome com collation ICU (empate "Água" antes de "Saúde"); `arredondar` na saída.
  > - Filtros só na ação `list`; `?mes=abc` → 400 no campo; id de outra conta → `[]`.
  > - S3 com `curl`: lista Feira, Mercado, Uber; totais `223.45` / Alimentação `200.00` (2) /
  >   Transporte `23.45` (1). Dados de teste excluídos.

**Checkpoint**: lista e totais pela API; suítes verdes.

---

## Phase 5: User Story 3 - Corrigir e excluir um gasto (Priority: P2)

**Goal**: alterar todos os campos e excluir, com as regras do lançamento e do mês fechado (FR-007,
FR-008).

**Independent Test**: quickstart S4.

### Tests for User Story 3 ⚠️

- [X] T018 [US3] Acrescentar a `backend/tests/gastos/test_gastos_api.py`:
  - `PATCH` de cada campo (descrição, valor, data, forma, categoria) → 200; `PUT` completo → 200;
  - `PATCH {"valor": "0"}` e `PATCH {"data": "2026-11-05"}` → mesmas mensagens do lançamento, nada muda;
  - mover para 11/2026 com data de novembro → 200; mover sem trocar a data → mensagem de data fora de 11/2026;
  - mês fechado: `PATCH` e `DELETE` → 400 de mês fechado, nada muda; mover de mês aberto para fechado e de fechado para aberto → 400;
  - `DELETE` em mês aberto → 204.

  Rodar e confirmar a **falha** nos casos de mês fechado (o resto deve passar com o `ModelViewSet`; registrar).

### Implementation for User Story 3

- [X] T019 [US3] Em `GastoViewSet`: `perform_update` chama `exigir_mes_aberto(instance.mes, validated_data.get("mes"))`; `perform_destroy` chama `exigir_mes_aberto(instance.mes)`. Confirmar T018 **verde**
- [X] T020 [US3] Validar o S4 do [quickstart.md](quickstart.md) com `curl` e limpar

  > **Resultado (2026-11-13)**: ✅ backend com 372 verdes (354 + 18); interface 85.
  > - T018: falharam primeiro só os 4 casos de mês fechado (alterar, excluir, mover para fechado
  >   e tirar de fechado), como previsto; os 14 de edição já passavam com o `ModelViewSet` e o
  >   `validate` da T010 (inclusive mover sem trocar a data → data fora de 11/2026).
  > - T019: `perform_update` confere o mês atual e o de destino; `perform_destroy`, o atual.
  > - S4 com `curl`: 200 `"25.00"`; fechar 200; alterar e excluir → 400 de mês fechado; reabrir
  >   200; excluir 204. Dados de teste excluídos.

**Checkpoint**: corrigir e excluir gastos; suítes verdes.

---

## Phase 6: User Story 4 - Proteger o histórico ao excluir mês ou categoria (Priority: P2)

**Goal**: mês com gastos não se exclui; categoria com gastos só com destino (FR-009, FR-010).

**Independent Test**: quickstart S5 e S6.

### Tests for User Story 4 ⚠️

- [X] T021 [P] [US4] Acrescentar a `backend/tests/gastos/test_gastos_service.py`: `verificar_exclusao_do_mes` lança `RegraViolada` com "Reabra o mês antes de excluí-lo." (fechado) e "Exclua ou mova os gastos antes de excluir o mês." (com gastos); aberto e vazio passa. `excluir_categoria(categoria, None)` sem gastos exclui; com gastos lança "Esta categoria tem gastos. Escolha outra categoria para recebê-los." e nada muda; com destino move todos os gastos (inclusive de mês fechado) e exclui; se a exclusão falhar depois de mover (simular com `monkeypatch`), nenhum gasto muda de categoria (atômico).
- [X] T022 [P] [US4] Acrescentar a `backend/tests/gastos/test_gastos_api.py` e `backend/tests/gastos/test_meses_api.py`: `DELETE` de mês com gastos → 400 com a mensagem; mês fechado continua com "Reabra o mês antes de excluí-lo."; `DELETE` de categoria com gastos sem `mover_para` → 400 `detail`; `?mover_para=` com a própria, inexistente, de outra conta ou `abc` → `400 {"mover_para": ["Escolha outra categoria sua para receber os gastos."]}`; válido → 204 e gastos na categoria destino; categoria sem gastos continua excluível (spec 006).

  Rodar e confirmar a **falha**.

### Implementation for User Story 4

- [X] T023 [US4] Implementar `verificar_exclusao_do_mes(mes)` e `excluir_categoria(categoria, destino)` (`transaction.atomic()`) em `backend/gastos/services/gastos.py`. Confirmar T021 **verde**
- [X] T024 [US4] Em `backend/gastos/views.py`: `MesReferenciaViewSet.perform_destroy` passa a chamar `verificar_exclusao_do_mes` (ponto de atenção 5); `CategoriaViewSet.destroy` resolve `mover_para` entre as categorias da pessoa (diferente da própria) e chama `excluir_categoria`. Confirmar T022 **verde** e as suítes de meses e categorias
- [X] T025 [US4] Validar o S5 e o S6 do [quickstart.md](quickstart.md) com `curl`

  > **Resultado (2026-11-13)**: ✅ backend com 387 verdes (372 + 7 do service + 8 da API);
  > interface 85.
  > - T021 falhou primeiro (funções inexistentes); T022 falhou nos 7 casos novos (o banco
  >   recusava com `RestrictedError`, que virava erro 500).
  > - T023: `verificar_exclusao_do_mes` (fechado, depois com gastos) e `excluir_categoria`
  >   (`@transaction.atomic`; com falha simulada na exclusão, os gastos voltam à categoria
  >   original).
  > - T024: a regra de mês fechado da spec 007 saiu da view para o service, com a mesma resposta
  >   (suíte de meses verde); `CategoriaViewSet.perform_destroy` resolve `mover_para` entre as
  >   categorias da pessoa, excluindo a própria.
  > - S5 com `curl`: mês com gastos → 400; categoria com gastos → 400 `detail`; destino = a própria
  >   → 400 `mover_para`; destino Outros → 204 e o gasto aparece em Outros. S6: Bia → 404, `[]`,
  >   404. Limpeza (S7): gasto e mês excluídos; Lazer (rosa) recriada para a Ana.

**Checkpoint**: histórico protegido; suítes verdes.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T026 [P] Atualizar o `README.md`: estado atual, rotas `/api/gastos/`, `/api/gastos/formas-pagamento/`, `/api/meses/<id>/totais/` e `?mover_para=`, e um parágrafo sobre gastos com link para o [contrato](contracts/api-gastos.md)
- [ ] T027 Executar o [quickstart.md](quickstart.md) completo (S1 a S7), deixar o banco local como antes e registrar
- [ ] T028 Fechar a Definition of Done: suítes verdes, tarefas marcadas, `makemigrations --check`; no `BACKLOG.md`: US-07 (critérios atendidos ☑, com nota de API), US-08 (3 critérios ☑; "confirmação antes de excluir" anotado para a US-27), US-05 (4º critério ☑ pela API; a escolha do destino na tela vai para a US-27), RNF-03 (2 primeiros critérios ☑); atualizar `DECISOES-AUTONOMAS.md`

**Checkpoint**: feature pronta para PR (depois da 007).

---

## Dependencies & Execution Order

```text
Setup → Foundational → US1 → US2 → US3 → US4 → Polish
```

- **Foundational** bloqueia tudo. **US1** cria serializer, viewset e rota; **US2**, **US3** e **US4**
  usam a API da US1. `services/gastos.py`, `views.py` e `test_gastos_api.py` são editados por
  várias fases, em sequência.

### Parallel Opportunities

- Foundational: T002 ∥ T003. US1: T007 ∥ T008. US2: T013 ∥ T014. US4: T021 ∥ T022.

## Implementation Strategy

MVP: Setup + Foundational + US1 + US2 (lançar e ver totais). Um checkpoint por fase.

## Notes

- Sem rebuild (nenhuma dependência nova); a migration roda na subida.
- Commits em pt-BR, Conventional Commits, sem trailers de IA; push a cada commit.

**Commit recomendado após cada checkpoint**:

| Checkpoint | Mensagem sugerida |
|---|---|
| T001 | `docs: especifica o lançamento de gastos (US-07 e US-08)` |
| T006 | `feat: adiciona o model de gasto e a regra de arredondamento` |
| T012 | `feat: adiciona API para lançar gastos (US1)` |
| T017 | `feat: adiciona lista de gastos e totais do mês (US2)` |
| T020 | `feat: permite corrigir e excluir gastos (US3)` |
| T025 | `feat: protege os gastos ao excluir mês ou categoria (US4)` |
| T028 | `docs: documenta os gastos e conclui US-07 e US-08` |
