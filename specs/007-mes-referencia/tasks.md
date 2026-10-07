---

description: "Lista de tarefas da feature 007-mes-referencia (US-06)"
---

# Tasks: Mês de Referência

**Input**: documentos de design em `/specs/007-mes-referencia/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/api-meses.md](contracts/api-meses.md),
[quickstart.md](quickstart.md)

**Tests**: **obrigatórios** (Princípio IV): model e API, com o kit de isolamento da spec 004.
Escreva os testes primeiro e confirme que falham. Se algum passar de primeira, registre na tarefa
e prove a falha de outro jeito (como na T022 da spec 006).

**Organization**: cada fase termina num **Checkpoint**: suítes verdes (`sh testar.sh`), resumo,
commit com a mensagem sugerida e push, sem trailers de IA (constituição v1.2.0). PR e merge ficam
com o responsável.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**:
  - US1: criar um mês
  - US2: ver os meses em ordem cronológica
  - US3: fechar e reabrir
  - US4: excluir
- Backend: `docker compose run --rm backend pytest` (219 hoje). Interface:
  `docker compose run --rm frontend npm test` (85 hoje, sem mudança nesta spec). Tudo:
  `sh testar.sh`.

---

## Phase 1: Setup

**Purpose**: linha de base verde antes de mexer.

- [X] T001 Subir o sistema (`docker compose up -d --wait`; ligar o Docker Desktop se estiver desligado) e rodar `sh testar.sh` (219 + 85 verdes) e `docker compose run --rm backend python manage.py makemigrations --check --dry-run` ("No changes detected")

  > **Resultado (2026-10-07)**: ✅ containers saudáveis; `sh testar.sh` verde (219 + 85);
  > `makemigrations --check` sem alterações. Os achados do analyze (I1, U1, C1, I2) serão
  > aplicados nas tarefas em que aparecem (T005, T007), com registro no resultado de cada uma.

**Checkpoint**: linha de base registrada; o commit leva os artefatos da spec (`specs/007-mes-referencia/`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: model `MesReferencia` com as regras no banco, e o helper de unicidade compartilhado
([research R-07](research.md)).

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T002 [P] Escrever **primeiro** `backend/tests/gastos/test_meses_models.py` ([data-model.md](data-model.md), [research R-01](research.md)), com `pytestmark = pytest.mark.django_db`:
  - `MesReferencia` herda de `OwnedModel`;
  - `mes` e `ano` são `PositiveSmallIntegerField`; `fechado` é `BooleanField` com `default=False`, e um mês criado só com `mes`, `ano` e `dono` nasce com `fechado is False`;
  - mesma conta, 10/2026 duas vezes → `IntegrityError` (dentro de `transaction.atomic()`), pela constraint `gastos_mes_unico_por_dono` (`UniqueConstraint(fields=["dono", "ano", "mes"])`);
  - contas diferentes: 10/2026 para Ana e para Bia → ambos criados;
  - `mes` 0 e 13 → `IntegrityError` pela `CheckConstraint` `gastos_mes_mes_valido` ("1 a 12"); `ano` 1999 e 2101 → `IntegrityError` pela `gastos_mes_ano_valido` ("2000 a 2100"); 1, 12, 2000 e 2100 são aceitos;
  - `MesReferencia.objects.do_dono(usuario)` vem em ordem cronológica: criados 03/2027, 12/2026 e 01/2026, nessa ordem → 01/2026, 12/2026, 03/2027 (`ordering = ["ano", "mes"]`);
  - `str(mes)` devolve `"MM/AAAA"` (ex.: `"03/2027"`).

  Rodar e confirmar a **falha** (model inexistente).
- [X] T003 Implementar `MesReferencia(OwnedModel)` em `backend/gastos/models.py`: `mes = PositiveSmallIntegerField()`, `ano = PositiveSmallIntegerField()`, `fechado = BooleanField(default=False)`; `Meta.ordering = ["ano", "mes"]`; `Meta.constraints` com `CheckConstraint(condition=Q(mes__gte=1, mes__lte=12), name="gastos_mes_mes_valido")`, `CheckConstraint(condition=Q(ano__gte=2000, ano__lte=2100), name="gastos_mes_ano_valido")` e `UniqueConstraint(fields=["dono", "ano", "mes"], name="gastos_mes_unico_por_dono", violation_error_message="Este mês já foi criado.")`; propriedade `rotulo` (`f"{self.mes:02d}/{self.ano}"`) usada pelo `__str__`. Gerar `backend/gastos/migrations/0003_mesreferencia.py` (`docker compose run --rm backend python manage.py makemigrations gastos --name mesreferencia`). Confirmar T002 **verde** e as guardas de isolamento da spec 004 verdes (o model novo é coberto sozinho)
- [X] T004 [P] Em `backend/gastos/views.py`, extrair o `_salvar` da `CategoriaViewSet` para a função de módulo `salvar_ou_erro_de_unicidade(salvar, erro)` ([research R-07](research.md)): roda `salvar()` dentro de `transaction.atomic()` e, num `IntegrityError`, lança `ValidationError(erro) from erro`. A `CategoriaViewSet` passa `{"nome": [MENSAGEM_NOME_REPETIDO]}`. Sem mudança de comportamento: confirmar `backend/tests/gastos/test_categorias_api.py` **verde**, incluindo o caso de corrida da spec 006

  > **Resultado (2026-10-07)**: ✅ backend com 231 verdes (219 + 12 do model); interface 85.
  > - T002 falhou primeiro (`MesReferencia` inexistente, erro na coleta).
  > - T003: `gastos.0003_mesreferencia` gerada com as duas `CheckConstraint` e a `UniqueConstraint`;
  >   aplicada na subida (`docker compose restart backend`); `makemigrations --check` sem
  >   pendências; guardas de isolamento da spec 004 verdes com o model novo.
  > - T004: `salvar_ou_erro_de_unicidade(salvar, erro)` no módulo `gastos/views.py`; a
  >   `CategoriaViewSet` usa `ERRO_NOME_REPETIDO`. Suíte de categorias verde, incluindo a corrida.
  > - Achado **I2** do analyze aplicado: T002 e T004 marcadas `[P]`.

**Checkpoint**: tabela `gastos_mesreferencia` criada na subida (`docker compose restart backend`); `makemigrations --check` sem pendências; suítes verdes.

---

## Phase 3: User Story 1 - Criar um mês (Priority: P1) 🎯 MVP

**Goal**: `POST /api/meses/` com faixas, mês único por conta e mensagens em português (FR-001,
FR-002, FR-008, FR-009).

**Independent Test**: quickstart S2; kit de isolamento verde.

### Tests for User Story 1 ⚠️

- [ ] T005 [US1] Escrever `backend/tests/gastos/test_meses_api.py` com `pytestmark = pytest.mark.django_db` e:
  - `TestIsolamentoMes(CasosDeIsolamento)` ([kit da spec 004](../../backend/tests/isolamento.py)): `modelo = MesReferencia`, `url_lista = "/api/meses/"`, `payload_criacao = {"mes": 10, "ano": 2026}`, `payload_alteracao = {"fechado": True}`, e `criar(usuario)` gerando **um mês diferente a cada chamada** (ex.: `n = MesReferencia.objects.count()`; `mes = n % 12 + 1`, `ano = 2026 + n // 12`), porque o mês é único por conta (ponto de atenção 2 do plano);
  - `POST {"mes": 10, "ano": 2026}` → 201 com exatamente `{"id": ..., "mes": 10, "ano": 2026, "rotulo": "10/2026", "fechado": False}` ([contrato](contracts/api-meses.md));
  - `POST {"mes": "10", "ano": "2026"}` (texto) → 201;
  - `POST {"mes": 10, "ano": 2026, "fechado": True}` → 201 com `"fechado": False` (o mês nasce aberto; FR-001);
  - repetir 10/2026 na mesma conta → 400 `{"non_field_errors": ["Este mês já foi criado."]}` e continua um só ([research R-03](research.md); ponto de atenção 1: confirmar que o DRF gera o `UniqueTogetherValidator` com a mensagem da constraint);
  - Bia criar 10/2026 com Ana já tendo 10/2026 → 201;
  - `mes` 0, 13, `"outubro"` e `"10.5"` → 400 `{"mes": ["Informe um mês de 1 a 12."]}`; `ano` 1999, 2101 e `"dois mil"` → 400 `{"ano": ["Informe um ano de 2000 a 2100."]}` ([research R-04](research.md)); `{"mes": 13, "ano": 1999}` → as duas mensagens de uma vez;
  - sem `mes`, sem `ano`, e com `""` em cada um → 400 `{"<campo>": ["Este campo é obrigatório."]}`;
  - `POST` sem sessão → 401.
- [ ] T006 [US1] Acrescentar a `backend/tests/gastos/test_meses_api.py` o caso de corrida ([research R-03](research.md)): com `monkeypatch` tirando a validação de unicidade do serializer (ex.: `MesReferenciaSerializer.get_validators` devolvendo `[]`), o `IntegrityError` da constraint vira 400 `{"non_field_errors": ["Este mês já foi criado."]}`, sem erro 500 e com um mês só.

  Rodar e confirmar a **falha** (rota inexistente).

### Implementation for User Story 1

- [ ] T007 [US1] Implementar `MesReferenciaSerializer(RegistroComDonoSerializer)` em `backend/gastos/serializers.py`: `fields = ["id", "mes", "ano", "rotulo", "fechado", "dono"]`; `mes = IntegerField(min_value=1, max_value=12, error_messages=...)` e `ano = IntegerField(min_value=2000, max_value=2100, error_messages=...)`, com `invalid`, `min_value` e `max_value` dizendo "Informe um mês de 1 a 12." / "Informe um ano de 2000 a 2100." e `required`/`null` dizendo "Este campo é obrigatório." (conferir que `""` cai em obrigatório; se cair em `invalid`, tratar para o contrato); `rotulo = CharField(read_only=True)`; `fechado` só leitura na criação (no `create`, forçar `fechado=False`). Exportar `MENSAGEM_MES_REPETIDO = "Este mês já foi criado."`
- [ ] T008 [US1] Implementar `MesReferenciaViewSet(FiltroPorDonoMixin, ModelViewSet)` em `backend/gastos/views.py` (`queryset = MesReferencia.objects.all()`), com `perform_create` e `perform_update` passando por `salvar_ou_erro_de_unicidade(..., {"non_field_errors": [MENSAGEM_MES_REPETIDO]})`; em `backend/gastos/urls.py`, `router.register("meses", MesReferenciaViewSet, basename="mes")`. Confirmar T005 e T006 **verdes**, e as guardas de rotas das specs 003 e 004 verdes
- [ ] T009 [US1] Validar o S2 do [quickstart.md](quickstart.md) com `curl` (Ana e Bia) e excluir os meses criados (S6)

**Checkpoint**: criar meses pela API, com isolamento comprovado; suítes verdes.

---

## Phase 4: User Story 2 - Ver os meses em ordem cronológica (Priority: P1)

**Goal**: `GET /api/meses/` em ordem crescente, com `rotulo` e `fechado` (FR-003).

**Independent Test**: quickstart S3.

### Tests for User Story 2 ⚠️

- [ ] T010 [US2] Acrescentar a `backend/tests/gastos/test_meses_api.py`:
  - criar 03/2027, 12/2026 e 01/2026, nessa ordem → `GET` devolve os rótulos `["01/2026", "12/2026", "03/2027"]` (atravessando o ano; SC-002);
  - cada item tem exatamente as chaves `{"id", "mes", "ano", "rotulo", "fechado"}` (sem `dono`);
  - conta sem meses → `[]`;
  - meses de Ana e de Bia → Ana vê só os dela (o kit já cobre; conferir).

  Rodar e registrar: é esperado que **passe de primeira** (a ordem vem do model, da T003). Nesse caso, provar a falha trocando temporariamente o `ordering` para `["-ano", "-mes"]` e restaurar (`git diff` vazio).

### Implementation for User Story 2

- [ ] T011 [US2] Se a T010 falhar em algum ponto, corrigir em `backend/gastos/serializers.py` ou `backend/gastos/models.py`. Validar o S3 do [quickstart.md](quickstart.md) com `curl` e limpar (S6)

**Checkpoint**: listagem cronológica comprovada; suítes verdes.

---

## Phase 5: User Story 3 - Fechar e reabrir um mês (Priority: P2)

**Goal**: `PATCH {"fechado": ...}`, mês e ano imutáveis e mês fechado sem exclusão (FR-004 a
FR-007).

**Independent Test**: quickstart S4 e S5.

### Tests for User Story 3 ⚠️

- [ ] T012 [US3] Acrescentar a `backend/tests/gastos/test_meses_api.py` ([research R-02 e R-05](research.md)):
  - `PATCH {"fechado": true}` → 200 com `"fechado": True`, e o `GET` do mês mostra fechado; `PATCH {"fechado": false}` → 200 aberto;
  - fechar um mês já fechado e reabrir um já aberto → 200, sem erro;
  - `PATCH {"mes": 11}` e `PATCH {"ano": 2027}` → 400 `{"<campo>": ["Não é possível alterar o mês ou o ano. Exclua o mês e crie de novo."]}`, e o mês continua 10/2026; vale também com o mês fechado;
  - `PATCH {"mes": 10, "ano": 2026, "fechado": true}` (mesmos valores) → 200; `PUT` com o objeto inteiro e os mesmos `mes`/`ano` → 200 (ponto de atenção 3 do plano);
  - `DELETE` de mês fechado → 400 `{"detail": "Reabra o mês antes de excluí-lo."}`, e o mês continua existindo (SC-003); depois de reabrir, `DELETE` → 204;
  - `fechado` com valor não booleano (ex.: `"talvez"`) → 400 no campo `fechado`.

  Rodar e confirmar a **falha** (mês e ano ainda alteráveis; exclusão de fechado ainda aceita).

### Implementation for User Story 3

- [ ] T013 [US3] Em `MesReferenciaSerializer` (`backend/gastos/serializers.py`): `validate_mes` e `validate_ano` recusam, numa edição (`self.instance is not None`), um valor **diferente** do atual com "Não é possível alterar o mês ou o ano. Exclua o mês e crie de novo."; o mesmo valor é aceito. Conferir que o `fechado` enviado é aplicado na edição
- [ ] T014 [US3] Em `MesReferenciaViewSet` (`backend/gastos/views.py`), `perform_destroy` recusa mês fechado com `ValidationError({"detail": "Reabra o mês antes de excluí-lo."})` (resposta `400 {"detail": "..."}`, sem lista; conferir o formato exato contra o [contrato](contracts/api-meses.md) e ajustar com `Response` se o DRF embrulhar em lista), deixando um comentário que a US-07 acrescenta aqui a regra de mês com gastos (FR-010). Confirmar T012 **verde**
- [ ] T015 [US3] Validar o S4 e o S5 do [quickstart.md](quickstart.md) com `curl` e limpar (S6)

**Checkpoint**: fechar e reabrir pela API, com as proteções; suítes verdes.

---

## Phase 6: User Story 4 - Excluir um mês (Priority: P3)

**Goal**: exclusão do próprio mês aberto (FR-010, sem a regra de gastos, que é da US-07).

**Independent Test**: suíte da API.

### Tests for User Story 4 ⚠️

- [ ] T016 [US4] Acrescentar a `backend/tests/gastos/test_meses_api.py`: `DELETE` de mês aberto → 204 e ele some da lista; depois de excluir 11/2026, criar 11/2026 de novo → 201 (corrigir é excluir e criar); `DELETE` de mês da Bia → 404 `{"detail": "Não encontrado."}` e ele continua existindo (o kit já cobre; conferir).

  Rodar e registrar: é esperado que **passe de primeira** (o `ModelViewSet` já tem `destroy`, e a T014 só recusa mês fechado). Nesse caso, provar a falha tirando temporariamente `"delete"` do `http_method_names` da viewset e restaurar (`git diff` vazio).
- [ ] T017 [US4] Se a T016 falhar em algum ponto, corrigir em `backend/gastos/views.py`. Rodar a suíte

**Checkpoint**: exclusão coberta por testes; suítes verdes.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T018 [P] Atualizar o `README.md`: "Estado atual" (meses de referência pela API; tela na US-27) e, na seção de rotas, `/api/meses/` com link para o [contrato](contracts/api-meses.md)
- [ ] T019 Executar o [quickstart.md](quickstart.md) completo (S1 a S6), deixar o banco local sem meses de teste e registrar o resultado
- [ ] T020 Fechar a Definition of Done:
  - suítes verdes e todas as tarefas marcadas; `makemigrations --check` sem pendências;
  - em `BACKLOG.md`, na US-06, marcar ☑ os 4 critérios, com nota no 4º: o estado "fechado" já existe e protege o mês contra exclusão; o bloqueio dos gastos vem com a US-07 e a US-08 (FR-007);
  - na US-07, acrescentar os critérios herdados "Um mês fechado não aceita novos gastos até ser reaberto." e "Um mês com gastos não pode ser excluído (\"Exclua ou mova os gastos antes de excluir o mês.\")." com a nota *(Herdado da US-06 na clarificação da spec 007-mes-referencia.)*, no mesmo formato do critério herdado da US-05.

**Checkpoint**: feature pronta para PR na `main`.

---

## Dependencies & Execution Order

```text
Setup → Foundational → US1 → US2 → US3 → US4 → Polish
```

- **Foundational** (model, migration e helper) bloqueia tudo.
- **US1** cria o serializer, a viewset e a rota; **US2**, **US3** e **US4** usam a API da US1.
  **US4** vem depois da US3 porque a T014 muda o `destroy` que a T016 confere.
- `backend/gastos/serializers.py`, `views.py` e `tests/gastos/test_meses_api.py` são editados por
  várias fases, sempre em sequência.

### Parallel Opportunities

- Foundational: T002 ∥ T004 (arquivos diferentes; T004 não depende do model).
- US1: T005 e T006 no mesmo arquivo: escrever em sequência, rodar juntos.
- Polish: T018 ∥ T019.

Pouco paralelismo: a spec é pequena e concentrada em três arquivos.

## Parallel Example: Foundational

```bash
Task: "T002 Testes do model MesReferencia em backend/tests/gastos/test_meses_models.py"
Task: "T004 Extrair salvar_ou_erro_de_unicidade em backend/gastos/views.py"
```

## Implementation Strategy

### MVP First

Setup + Foundational + US1 + US2: criar e listar meses pela API. A US-07 (gastos) já pode começar
daí; a US3 entrega o "fechado" que a US-07 e a US-08 consultam.

### Incremental Delivery

Um checkpoint por fase, com `sh testar.sh` verde.

## Notes

- **Kit de isolamento com mês único**: o `criar(usuario)` da subclasse precisa gerar meses
  diferentes, senão o próprio kit esbarra na constraint (T005).
- **Sem tela**: a interface não muda; a suíte do frontend continua com 85.
- **Sem rebuild**: nenhuma dependência nova; o backend é montado. A migration roda na subida
  (`docker compose restart backend`).
- Commits em pt-BR, Conventional Commits, **sem** `Co-Authored-By` nem rodapés de IA; push a cada
  commit (constituição v1.2.0).

**Commit recomendado após cada checkpoint (T001, T004, T009, T011, T015, T017, T020)**:

| Checkpoint | Mensagem sugerida |
|---|---|
| T001 | `docs: especifica o mês de referência (US-06)` |
| T004 | `feat: adiciona o model de mês de referência` |
| T009 | `feat: adiciona API para criar meses de referência (US1)` |
| T011 | `test: cobre a ordem cronológica dos meses (US2)` |
| T015 | `feat: permite fechar e reabrir meses (US3)` |
| T017 | `test: cobre a exclusão de meses (US4)` |
| T020 | `docs: documenta os meses de referência e conclui US-06` |

O primeiro commit (T001) leva os artefatos da spec (`specs/007-mes-referencia/`).
