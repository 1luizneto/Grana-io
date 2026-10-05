---

description: "Lista de tarefas da feature 004-isolamento-usuario (US-03)"
---

# Tasks: Isolamento de Dados por Usuário

**Input**: documentos de design em `/specs/004-isolamento-usuario/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/isolamento.md](contracts/isolamento.md),
[quickstart.md](quickstart.md)

**Tests**: **obrigatórios** pelo Princípio IV. Isolamento é core. Escreva os testes primeiro e
confirme que falham. Se algum teste passar de primeira porque uma fase anterior já entregou o
comportamento, registre isso na tarefa (como na spec 003). `settings_test.py` e `pytest.ini` são
glue, validados pela suíte e pelo [quickstart.md](quickstart.md).

**Organization**: cada fase termina num **Checkpoint**. No checkpoint, pare com a suíte verde,
apresente o resumo, faça o commit com a mensagem sugerida e o push (sem trailers de IA). PR e
merge ficam com o responsável.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**:
  - US1: ver só os próprios registros
  - US2: registro de outra pessoa tratado como inexistente
  - US3: o dono é sempre quem está conectado
  - US4: todo registro novo já nasce isolado (guardas)
- Suíte: `docker compose run --rm backend pytest`. **Ligar o Docker Desktop antes de começar.**

---

## Phase 1: Setup

**Purpose**: settings de teste, app de exemplo vazio, fixtures compartilhadas e helper de rotas.

- [X] T001 Criar `backend/config/settings_test.py` com `from config.settings import *  # noqa: F403` e `INSTALLED_APPS = [*INSTALLED_APPS, "tests.exemplo"]`. Em `backend/pytest.ini`, trocar `DJANGO_SETTINGS_MODULE` para `config.settings_test` ([research R-07](research.md))
- [X] T002 Criar o app de exemplo **sem pasta `migrations`** (depois ganhou migration na T009) em `backend/tests/exemplo/`:
  - `__init__.py` vazio;
  - `apps.py` com `ExemploConfig(AppConfig)`, `name = "tests.exemplo"`, `label = "exemplo"`, `default_auto_field = "django.db.models.BigAutoField"`;
  - `models.py` só com o import de `models` (os models entram na T009).
- [X] T003 [P] Mover as fixtures `usuario`, `outro_usuario`, `cliente` e `cliente_autenticado` (e a constante `SENHA`) de `backend/tests/accounts/conftest.py` para `backend/tests/conftest.py`, **sem mudar nomes nem valores**. Acrescentar `cliente_da_bia`: `APIClient` com `force_authenticate(user=outro_usuario)`. Apagar `backend/tests/accounts/conftest.py` se ficar vazio; ajustar imports de `SENHA` nos testes de accounts, se houver ([research R-09](research.md))
- [X] T004 [P] Extrair a função `_rotas(padroes, prefixo="")` de `backend/tests/accounts/test_protecao_api.py` para `backend/tests/rotas.py` com o nome público `rotas(padroes, prefixo="")`, e fazer o `test_protecao_api.py` importá-la. A guarda de proteção continua usando `get_resolver()` do `ROOT_URLCONF` real
- [X] T005 Rodar a suíte e confirmar **126 testes verdes** com o `settings_test`. Rodar `docker compose run --rm backend python manage.py makemigrations --check --dry-run` (settings de uso) e conferir "No changes detected"

  > **Resultado (2026-10-05)**: ✅ 126 testes verdes com `config.settings_test` (10 s);
  > `makemigrations --check` com o settings de uso: "No changes detected". O
  > `tests/accounts/conftest.py` foi apagado (ficou vazio), e os 3 testes que importavam `SENHA`
  > dele passaram a importar de `tests.conftest`.

**Checkpoint**: suíte verde com o settings de teste; nada mudou na aplicação.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: a base `OwnedModel` e os models de exemplo que todas as histórias usam.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T006 Escrever **primeiro** `backend/tests/core/test_owned_model.py` (usando `ItemExemplo` e `GrupoExemplo` de `tests.exemplo.models`):
  - `OwnedModel._meta.abstract` é `True`;
  - o campo `dono` é FK para `settings.AUTH_USER_MODEL`, `editable is False`, `remote_field.on_delete is CASCADE`, `remote_field.related_name == "+"`, e está indexado (`db_index`);
  - `ItemExemplo.objects.do_dono(usuario)` devolve só os itens de Ana, com itens de Ana e de Bia no banco;
  - criar `ItemExemplo` sem dono lança `IntegrityError`;
  - excluir a conta de Bia remove os registros dela e mantém os de Ana (FR-012);
  - `GrupoExemplo` com o mesmo `nome` é aceito para Ana e Bia, e recusado com `IntegrityError` na mesma conta (FR-007).

  Toda operação que deve lançar `IntegrityError` fica dentro de `with transaction.atomic():` (dentro do `pytest.raises`), e as verificações seguintes vêm depois do bloco. Sem isso, o PostgreSQL invalida a transação do teste.

  Rodar e confirmar a **falha** (import inexistente).
- [X] T007 Implementar em `backend/core/models.py` ([research R-01](research.md); [data-model.md](data-model.md)):
  - `RegistroDoDonoQuerySet(models.QuerySet)` com `do_dono(self, usuario)` → `self.filter(dono=usuario)`;
  - `OwnedModel(models.Model)` abstrato com `dono = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+", editable=False)` e `objects = RegistroDoDonoQuerySet.as_manager()`. Docstring citando a constituição (Princípio II) e o contrato.
- [X] T008 Conferir que `backend/core/` continua sem `migrations` necessárias (`OwnedModel` é abstrato): `makemigrations --check --dry-run` sem alterações
- [X] T009 Implementar os models de exemplo em `backend/tests/exemplo/models.py` ([data-model.md](data-model.md)):
  - `GrupoExemplo(OwnedModel)`: `nome = CharField(max_length=60)`; `Meta.constraints = [UniqueConstraint(fields=["dono", "nome"], name="exemplo_grupo_nome_por_dono", violation_error_message="Já existe um grupo com este nome.")]`; `ordering = ["id"]`;
  - `ItemExemplo(OwnedModel)`: `descricao = CharField(max_length=100)`; `valor = DecimalField(max_digits=12, decimal_places=2)`; `grupo = ForeignKey(GrupoExemplo, null=True, blank=True, on_delete=SET_NULL, related_name="itens")`; `ordering = ["id"]`.

  Rodar a suíte e confirmar T006 **verde**. Confirmar o ponto de atenção 3 do plano: o banco de testes cria as tabelas sem migration e o `test_nao_ha_migrations_pendentes` (agora com `settings_test`) continua verde. Se não continuar, criar a migration inicial de `tests/exemplo` e registrar aqui.

  > **Resultado (2026-10-05)**: ✅ 132 testes verdes (126 + 6 da T006).
  > - T006 falhou primeiro na coleta (import de `core.models` inexistente).
  > - **Ponto de atenção 3**: o app sem migration **não funcionou**. O Django cria as tabelas de
  >   apps sem migration antes de aplicar as migrations, e a FK `dono` falhou com "relation
  >   accounts_usuario does not exist". Plano B aplicado: `tests/exemplo/migrations/0001_initial.py`,
  >   gerada com o `settings_test`. Research R-07, data-model e plan atualizados.
  > - `makemigrations --check` sem alterações com os dois settings. No banco de uso: nenhuma
  >   tabela `exemplo_*` e nenhuma linha `exemplo` em `django_migrations`.
  > - T008: o `core` continua sem migrations (`OwnedModel` é abstrato).

**Checkpoint**: `OwnedModel` pronto, exemplo com tabelas só no banco de testes, suíte verde.

---

## Phase 3: User Story 1 - Ver só os próprios registros (Priority: P1) 🎯 MVP

**Goal**: listas, buscas e totais devolvem só os registros da conta conectada (FR-004, FR-008).

**Independent Test**: com itens de Ana e de Bia, cada uma lista, busca e soma só os seus (quickstart S2, parte de listas).

### Tests for User Story 1 ⚠️

- [ ] T010 [P] [US1] Criar o kit em `backend/tests/isolamento.py` ([research R-08](research.md)) com a classe base `CasosDeIsolamento` (sem prefixo `Test`, para o pytest não coletá-la sozinha). Atributos que a subclasse define: `url_lista`; `url_detalhe(self, pk)`; `criar(self, usuario)` (devolve um registro do usuário); `payload_criacao`; `payload_alteracao`. Casos desta história:
  - `test_lista_so_do_dono`: 2 registros de Ana e 1 de Bia; Ana lista e recebe exatamente os ids dos seus;
  - `test_lista_vazia_sem_pistas`: só Bia tem registros; Ana recebe 200 e `[]`.

  Usar as fixtures `usuario`, `outro_usuario`, `cliente_autenticado` e `cliente_da_bia` (T003).
- [ ] T011 [P] [US1] Criar `backend/tests/exemplo/test_isolamento_exemplo.py` com `pytestmark = [pytest.mark.django_db, pytest.mark.urls("tests.exemplo.urls")]` e:
  - `TestIsolamentoItemExemplo(CasosDeIsolamento)`, com `url_lista = "/api/exemplo/itens/"`, `criar` via ORM e payloads com `descricao` e `valor`;
  - `test_busca_so_do_dono`: Ana e Bia têm itens com "mercado" na descrição; `?busca=mercado` para Ana devolve só os dela;
  - `test_total_so_do_dono`: Ana tem itens de `Decimal("10.00")` e `Decimal("20.00")`, e Bia um de `Decimal("99.00")`; `GET /api/exemplo/itens/total/` para Ana devolve `{"quantidade": 2, "soma": "30.00"}`;
  - `test_sem_sessao_e_recusado`: sem autenticação, a lista responde 401 (spec 003) e nenhum dado vaza.

  Rodar e confirmar a **falha** (rotas inexistentes).

### Implementation for User Story 1

- [ ] T012 [US1] Implementar `backend/core/mixins.py` com `FiltroPorDonoMixin` ([research R-02](research.md)):
  - `get_queryset()` → `super().get_queryset().do_dono(self.request.user)`;
  - `perform_create(serializer)` → `serializer.save(dono=self.request.user)`.

  Docstring: o mixin vem **antes** da classe do DRF na herança.
- [ ] T013 [US1] Criar `backend/tests/exemplo/serializers.py` com `ItemExemploSerializer(ModelSerializer)`, `fields = ["id", "descricao", "valor", "grupo"]` (a base com dono entra na US3, T024)
- [ ] T014 [US1] Criar `backend/tests/exemplo/views.py` com `ItemExemploViewSet(FiltroPorDonoMixin, ModelViewSet)`: `queryset = ItemExemplo.objects.all()`; `serializer_class = ItemExemploSerializer`; `filter_backends = [BuscaFilter]`, onde `BuscaFilter(SearchFilter)` (no mesmo arquivo) define `search_param = "busca"`; `search_fields = ["descricao"]`; e a ação `@action(detail=False) total`, que responde `{"quantidade": n, "soma": "<Decimal com 2 casas>"}` calculado sobre `self.filter_queryset(self.get_queryset())`
- [ ] T015 [US1] Criar `backend/tests/exemplo/urls.py`: `urlpatterns = [*config.urls.urlpatterns, path("api/exemplo/", include(router.urls))]`, com `DefaultRouter(trailing_slash=True)` registrando `itens` → `ItemExemploViewSet`. Rodar a suíte e confirmar T010 e T011 **verdes**

**Checkpoint**: listas, busca e total isolados por dono; suíte verde.

---

## Phase 4: User Story 2 - Registro de outra pessoa é tratado como inexistente (Priority: P1)

**Goal**: abrir, alterar ou excluir registro de outra conta dá o mesmo 404 de um id inexistente, sem alterar nada (FR-005).

**Independent Test**: Bia cria um item; Ana tenta ler, alterar e excluir; as três respostas são iguais à de um id inexistente, e o item continua intacto (quickstart S2).

### Tests for User Story 2 ⚠️

- [ ] T016 [US2] Acrescentar ao kit `backend/tests/isolamento.py`:
  - `test_abrir_de_outra_conta_igual_a_inexistente`: `GET` no registro de Bia, feito por Ana, tem o mesmo `status_code` (404) e o mesmo `json()` de um `GET` num id inexistente (`registro_de_bia.pk + 1000`);
  - `test_alterar_de_outra_conta_nao_muda_nada`: `PATCH` com `payload_alteracao` → 404 idêntico; `refresh_from_db()` mostra o registro igual ao original;
  - `test_excluir_de_outra_conta_nao_exclui`: `DELETE` → 404 idêntico; o registro continua existindo;
  - `test_dono_opera_normalmente`: Ana abre (200), altera (200) e exclui (204) o próprio registro; um novo `GET` nele, pela própria Ana, dá 404 (caso de borda "registro excluído pelo dono").
- [ ] T017 [US2] Acrescentar a `backend/tests/exemplo/test_isolamento_exemplo.py`:
  - `test_id_mal_formado_e_nao_encontrado`: `GET /api/exemplo/itens/abc/` → 404 com o mesmo corpo do id inexistente;
  - `test_texto_do_nao_encontrado`: o corpo é `{"detail": "Não encontrado."}` (ponto de atenção 4 do plano; se o texto for outro, ajustar o teste e o [contrato](contracts/isolamento.md)).

  Rodar e registrar o resultado. É esperado que estes testes **passem de primeira**, porque o filtro da T012 já entrega o comportamento; nesse caso, confirmar a falha retirando temporariamente o `FiltroPorDonoMixin` da viewset e registrar.

### Implementation for User Story 2

- [ ] T018 [US2] Se algum caso da T016/T017 falhar, corrigir no `FiltroPorDonoMixin` (`backend/core/mixins.py`), nunca na viewset de exemplo. Se o router recusar `abc` antes da view (404 do Django em vez do DRF), garantir que a resposta seja idêntica à do id inexistente (ex.: `lookup_value_regex` no mixin) e registrar a decisão
- [ ] T019 [US2] Rodar a suíte e confirmar T016 e T017 **verdes**

**Checkpoint**: registro de outra conta é indistinguível de inexistente; suíte verde.

---

## Phase 5: User Story 3 - O dono é sempre quem está conectado (Priority: P1)

**Goal**: dono vem da sessão, é ignorado no payload, não muda depois; referências só para registros do mesmo dono; unicidade por conta (FR-002, FR-003, FR-006, FR-007).

**Independent Test**: Ana cria um item dizendo que o dono é Bia, e o item é de Ana; aponta para um grupo de Bia, e é recusada com "Registro não encontrado." (quickstart S2).

### Tests for User Story 3 ⚠️

- [ ] T020 [P] [US3] Acrescentar ao kit `backend/tests/isolamento.py`:
  - `test_dono_do_payload_ignorado_na_criacao`: Ana faz `POST` com `{**payload_criacao, "dono": outro_usuario.pk}` → 201; o registro criado tem `dono == usuario`; a resposta **não** contém a chave `dono`;
  - `test_dono_do_payload_ignorado_na_alteracao`: Ana faz `PATCH` no próprio registro com `{"dono": outro_usuario.pk}` → 200; o dono continua Ana.
- [ ] T021 [P] [US3] Escrever `backend/tests/core/test_serializers_dono.py` (com `ItemExemplo`/`GrupoExemplo`). Montar o contexto com `request = APIRequestFactory().post("/")`, depois `request.user = usuario`, e passar `context={"request": request}` aos serializers (o `CurrentUserDefault` e o `RelacionadoDoDonoField` leem `request.user`):
  - `RegistroComDonoSerializer`: `dono` é `HiddenField` e não aparece em `.data`; `validated_data["dono"]` é o usuário do `request` mesmo com `dono` no payload;
  - `RelacionadoDoDonoField`: aceita o grupo de Ana para Ana; recusa o grupo de Bia e um id inexistente com **a mesma** mensagem `"Registro não encontrado."`.
- [ ] T022 [US3] Acrescentar a `backend/tests/exemplo/test_isolamento_exemplo.py`:
  - `TestIsolamentoGrupoExemplo(CasosDeIsolamento)`, com `url_lista = "/api/exemplo/grupos/"` e payloads com `nome`;
  - `test_item_com_grupo_de_outra_conta_e_recusado`: `POST` de item com o `grupo` de Bia → 400 `{"grupo": ["Registro não encontrado."]}`; mesma resposta para grupo inexistente;
  - `test_nome_de_grupo_repetido_entre_contas_e_aceito`: Ana e Bia criam "Mercado" → 201 e 201;
  - `test_nome_de_grupo_repetido_na_mesma_conta_e_recusado`: Ana cria "Mercado" duas vezes → 400 com mensagem em pt-BR que **não** contém "dono" (ponto de atenção 2 do plano).

  Rodar e confirmar a **falha**.

### Implementation for User Story 3

- [ ] T023 [US3] Implementar `backend/core/serializers.py` ([research R-03, R-04, R-05](research.md)):
  - `RegistroComDonoSerializer(ModelSerializer)` com `dono = HiddenField(default=CurrentUserDefault())`. Verificar se o `UniqueTogetherValidator` gerado para `UniqueConstraint(dono, ...)` usa a `violation_error_message`; se não usar, sobrescrever `get_validators()` para trocar a mensagem dos validadores que envolvem `dono` pela `violation_error_message` da constraint, e registrar a decisão nesta tarefa;
  - `RelacionadoDoDonoField(PrimaryKeyRelatedField)`, cujo `get_queryset()` aplica `.do_dono(self.context["request"].user)` sobre o queryset declarado, com `default_error_messages` `does_not_exist` e `incorrect_type` = `"Registro não encontrado."`.
- [ ] T024 [US3] Em `backend/tests/exemplo/serializers.py`:
  - `ItemExemploSerializer` passa a herdar de `RegistroComDonoSerializer`, com `grupo = RelacionadoDoDonoField(queryset=GrupoExemplo.objects.all(), allow_null=True, required=False)` e `fields = ["id", "descricao", "valor", "grupo", "dono"]` (o `dono` oculto precisa estar em `fields`);
  - `GrupoExemploSerializer(RegistroComDonoSerializer)`, com `fields = ["id", "nome", "dono"]`.
- [ ] T025 [US3] Em `backend/tests/exemplo/views.py` e `urls.py`, criar `GrupoExemploViewSet(FiltroPorDonoMixin, ModelViewSet)` e registrar `grupos` no router. Rodar a suíte e confirmar T020, T021 e T022 **verdes**

**Checkpoint**: dono definido pelo servidor, referências e unicidade isoladas; suíte verde.

---

## Phase 6: User Story 4 - Todo registro novo já nasce isolado (Priority: P2)

**Goal**: a suíte falha se surgir model do projeto sem dono ou view sobre `OwnedModel` sem o mixin (FR-010; SC-004).

**Independent Test**: quickstart S3 e S4 (acrescentar um model sem dono ou tirar o mixin faz a guarda falhar apontando o culpado).

### Tests for User Story 4 ⚠️

- [ ] T026 [US4] Escrever `backend/tests/core/test_guarda_isolamento.py` ([research R-06](research.md)):
  - `test_funcao_aponta_model_sem_dono`: `modelos_sem_dono([Usuario, ItemExemplo], excecoes=set())` devolve `["accounts.Usuario"]` (caso negativo da US4, cenário 1);
  - `test_funcao_respeita_excecoes`: com `excecoes={"accounts.Usuario"}`, devolve `[]`;
  - `test_guarda_todo_model_do_projeto_tem_dono`: aplica `modelos_sem_dono` a todos os models concretos de apps cujo `path` está dentro de `settings.BASE_DIR`, com `MODELS_SEM_DONO = {"accounts.Usuario"}`, e exige `[]`; a mensagem de falha lista os models e lembra que exceções só valem para dados de referência compartilhados (constituição v1.2.0, Princípio II), com comentário citando a spec. Declarar `MODELS_SEM_DONO` no topo do arquivo, com comentário `# accounts.Usuario: é o próprio dono (spec 004)`;
  - `test_guarda_toda_view_de_registro_com_dono_usa_o_filtro` (com `@pytest.mark.urls("tests.exemplo.urls")`): percorre `rotas(get_resolver().url_patterns)` (helper `rotas()` de `backend/tests/rotas.py`, T004); para toda view cujo `cls` (ou `view_class`) tem `queryset.model` subclasse de `OwnedModel`, exige `issubclass(view, FiltroPorDonoMixin)`; a mensagem lista as rotas.

  Rodar e confirmar a **falha** (função inexistente).

### Implementation for User Story 4

- [ ] T027 [US4] Implementar `modelos_sem_dono(models, excecoes) -> list[str]` em `backend/tests/isolamento.py`: devolve, ordenados, os `"<app_label>.<ModelName>"` de models concretos (não abstratos, não proxy) que não herdam de `OwnedModel` e não estão em `excecoes`. Rodar e confirmar T026 **verde**
- [ ] T028 [US4] Validar os cenários S3 e S4 do [quickstart.md](quickstart.md) (experimentos temporários: `Rascunho` sem dono e viewset sem mixin), registrar as mensagens de falha obtidas e **desfazer** os dois experimentos. Suíte verde ao final

**Checkpoint**: guardas de models e de rotas ativas e demonstradas; suíte verde.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T029 [P] Atualizar `docs/arquitetura.md` §2.2, linha "Abstract Base Model + Mixin": citar os nomes finais (`OwnedModel`/`do_dono`, `FiltroPorDonoMixin`, `RegistroComDonoSerializer`, `RelacionadoDoDonoField`), a convenção `UniqueConstraint(dono, ...)`, o kit `tests/isolamento.py` e o [contrato de isolamento](contracts/isolamento.md) como referência para os endpoints de dados. Commit `docs:` próprio não é necessário: entra no marco final
- [ ] T030 [P] Atualizar o `README.md`: no "Estado atual", a US-03; numa nota para quem desenvolve, como criar um registro de dados isolado (herdar `OwnedModel`, usar o mixin e o serializer base, escrever a subclasse de `CasosDeIsolamento`), com link para o contrato
- [ ] T031 Executar o [quickstart.md](quickstart.md) completo (S1 a S6) e registrar o resultado. Conferir também `makemigrations --check` com o settings de uso e a ausência de tabelas `exemplo_*` no banco de uso
- [ ] T032 Fechar a Definition of Done:
  - suíte verde e todas as tarefas marcadas;
  - em `BACKLOG.md`, na US-03, marcar ☑ os 4 critérios, com nota: "garantido pela base `OwnedModel` e pelas guardas; cada US de dados (US-05 em diante) confirma com o kit de isolamento";
  - no RNF-05, deixar ☐ "Os endpoints da API têm testes de integração, incluindo o isolamento entre usuários", com nota de que o kit existe e cada US de dados o aplica.

**Checkpoint**: feature pronta para PR na `main`.

---

## Dependencies & Execution Order

```text
Setup → Foundational → US1 → US2 → US3 → US4 → Polish
```

- **Foundational** (`OwnedModel` + models de exemplo) bloqueia tudo.
- **US1** cria o mixin, a viewset de itens e o kit; **US2** e **US3** estendem o kit e o exemplo.
- **US2** depende só da US1. **US3** depende da US1 (mixin, viewset) e pode vir antes da US2, mas
  as duas editam o kit e o arquivo de testes do exemplo, então rodam em sequência.
- **US4** depende da US1 (mixin, helper de rotas) e fica completa depois da US3 (viewset de
  grupos também passa pela guarda).
- `backend/tests/isolamento.py`, `backend/tests/exemplo/test_isolamento_exemplo.py`,
  `serializers.py`, `views.py` e `urls.py` do exemplo são editados por várias fases, sempre em
  sequência.

### Parallel Opportunities

- Setup: T003 ∥ T004.
- US1: T010 ∥ T011.
- US3: T020 ∥ T021.
- Polish: T029 ∥ T030.

## Parallel Example: User Story 3

```bash
Task: "T020 Casos de dono ignorado no kit backend/tests/isolamento.py"
Task: "T021 Testes dos serializers base em backend/tests/core/test_serializers_dono.py"
```

## Implementation Strategy

### MVP First

Setup + Foundational + US1 + US2 + US3: a regra de dono completa (filtro, 404 e dono pelo
servidor), suficiente para a US-05 começar. A US4 (guardas) protege as USs seguintes contra
esquecimento.

### Incremental Delivery

Um checkpoint por fase, cada um com a suíte verde. Como não há rota nova na aplicação, a validação
é pela suíte e pelo quickstart.

## Notes

- **Sem rebuild**: nenhuma dependência nova; o código do backend é montado no container.
- **O app `tests.exemplo` nunca entra no `config/settings.py`** (FR-013). A migration dele
  (T009) fica dentro de `tests/exemplo/migrations/` e só roda no banco de testes.
- Commits em pt-BR, Conventional Commits, **sem** `Co-Authored-By` nem rodapés de IA; push a cada
  commit. O assistente commita com autorização do responsável (constituição v1.2.0); PR e merge
  são do responsável.

**Commit recomendado após cada checkpoint (T005, T009, T015, T019, T025, T028, T032)**:

| Checkpoint | Mensagem sugerida |
|---|---|
| T005 | `chore: adiciona settings de teste e app de exemplo só para testes` |
| T009 | `feat: adiciona base OwnedModel com dono e filtro do_dono` |
| T015 | `feat: filtra listas, buscas e totais pelo dono (US1)` |
| T019 | `test: garante 404 idêntico para registro de outra conta (US2)` |
| T025 | `feat: define o dono pela sessão e isola referências e unicidade (US3)` |
| T028 | `test: adiciona guardas de isolamento para models e rotas (US4)` |
| T032 | `docs: documenta a regra de dono e conclui US-03` |

O primeiro commit (T005) também inclui os artefatos da spec (`specs/004-isolamento-usuario/`) e a
emenda v1.2.0 da constituição (`.specify/memory/constitution.md`, achados D1 e D2 do
`/speckit-analyze`).
