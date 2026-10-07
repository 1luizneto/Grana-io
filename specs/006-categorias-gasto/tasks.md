---

description: "Lista de tarefas da feature 006-categorias-gasto (US-05 + critério de categorias padrão da US-01)"
---

# Tasks: Categorias de Gasto

**Input**: documentos de design em `/specs/006-categorias-gasto/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/api-categorias.md](contracts/api-categorias.md),
[contracts/tela-categorias.md](contracts/tela-categorias.md), [quickstart.md](quickstart.md)

**Tests**: **obrigatórios** (Princípio IV): model, service, migration de dados, API (com o kit de
isolamento da spec 004) e a tela (lógica e erros, como na spec 005). Escreva os testes primeiro e
confirme que falham; se algum passar de primeira, registre na tarefa.

**Organization**: cada fase termina num **Checkpoint**: suítes verdes (`sh testar.sh`), resumo,
commit com a mensagem sugerida e push, sem trailers de IA (constituição v1.2.0). PR e merge ficam
com o responsável.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**:
  - US1: categorias padrão (cadastro e contas antigas)
  - US2: criar e renomear
  - US3: cor (paleta e cor automática)
  - US4: excluir
  - US5: tela de categorias
- Backend: `docker compose run --rm backend pytest` (165 hoje). Interface:
  `docker compose run --rm frontend npm test` (69 hoje). Tudo: `sh testar.sh`.

---

## Phase 1: Setup

**Purpose**: app `gastos` vazio, registrado e com rota.

- [X] T001 Criar o app `backend/gastos/` ([research R-01](research.md)): `__init__.py`, `apps.py` (`GastosConfig`, `name = "gastos"`, `default_auto_field = "django.db.models.BigAutoField"`), `models.py` só com o import de `models`, `migrations/__init__.py`, `urls.py` com `urlpatterns = []`. Acrescentar `"gastos"` ao `INSTALLED_APPS` de `backend/config/settings.py`, depois de `"core"`, e `path("api/", include("gastos.urls"))` em `backend/config/urls.py`. Criar `backend/tests/gastos/__init__.py`
- [X] T002 Rodar `sh testar.sh` (165 + 69 verdes) e `docker compose run --rm backend python manage.py makemigrations --check --dry-run` ("No changes detected")

  > **Resultado (2026-10-07)**: ✅ `sh testar.sh` verde (165 + 69); `makemigrations --check` sem
  > alterações. O Docker Desktop estava desligado e foi ligado antes da T001.

**Checkpoint**: app registrado, nada muda para quem usa.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: paleta e model `Categoria`, base de todas as histórias.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T003 [P] Escrever **primeiro** `backend/tests/gastos/test_cores.py` ([research R-02](research.md)): `PALETA` tem 12 cores, na ordem e com os códigos, nomes e hex exatos da tabela do R-02; códigos únicos; todo hex no formato `#RRGGBB`; `CODIGOS` é a lista de códigos na mesma ordem; `obter_cor("verde").nome == "Verde"`.
- [X] T004 [P] Escrever **primeiro** `backend/tests/gastos/test_models.py` ([data-model.md](data-model.md)):
  - `Categoria` herda de `OwnedModel`;
  - `nome` é `CharField(max_length=50)`; `cor` é `CharField(max_length=20)` com `choices` iguais à paleta;
  - mesma conta: "Pets" e depois "pets" → `IntegrityError` (dentro de `transaction.atomic()`), pela constraint `gastos_categoria_nome_por_dono` (`UniqueConstraint(Lower("nome"), "dono")`);
  - contas diferentes: "Pets" para Ana e para Bia → ambas criadas;
  - "Saude" e "Saúde" na mesma conta → ambas criadas (acento conta);
  - `Categoria.objects.do_dono(usuario)` vem em ordem alfabética sem diferenciar maiúsculas ("alimentação", "Banco", "casa").

  Rodar e confirmar a **falha**.
- [X] T005 Implementar `backend/gastos/cores.py`: `Cor = namedtuple("Cor", "codigo nome hex")`, `PALETA` (tupla na ordem do R-02), `CODIGOS`, `CHOICES = [(c.codigo, c.nome) for c in PALETA]` e `obter_cor(codigo)`. Confirmar T003 **verde**
- [X] T006 Implementar `Categoria(OwnedModel)` em `backend/gastos/models.py`: `nome = CharField(max_length=50)`, `cor = CharField(max_length=20, choices=CHOICES)`; `Meta.ordering = [Lower("nome")]`; `Meta.constraints = [UniqueConstraint(Lower("nome"), "dono", name="gastos_categoria_nome_por_dono", violation_error_message="Já existe uma categoria com este nome.")]`; `__str__` devolve o nome. Gerar `backend/gastos/migrations/0001_initial.py` (`docker compose run --rm backend python manage.py makemigrations gastos`). Confirmar T004 **verde** e a guarda de models da spec 004 verde (o app novo é coberto sozinho)

  > **Resultado (2026-10-07)**: ✅ backend com 175 verdes (165 + 4 da paleta + 6 do model).
  > - T003 e T004 falharam primeiro (módulos inexistentes).
  > - **Achado U1 do analyze, confirmado**: a collation padrão do banco ordena "Água" e "Ônibus"
  >   depois de "zebra". A T004 ganhou o caso com acentos e a T006 ordena com
  >   `Collate(Lower("nome"), "und-x-icu")`. Registrado como research R-10; data-model ajustado.
  > - `gastos.0001_initial` aplicada na subida do backend (`docker compose restart backend`);
  >   `makemigrations --check` sem pendências; guardas de isolamento verdes com o app novo.

**Checkpoint**: tabela `gastos_categoria` criada na subida; suítes verdes.

---

## Phase 3: User Story 1 - Começar com categorias prontas (Priority: P1) 🎯 MVP

**Goal**: conta nova e contas antigas com as 7 categorias padrão, sem duplicar (FR-001, FR-002).

**Independent Test**: quickstart S2 e S3 (S3 completo depois da US5; até lá, pela API ou pelo banco).

### Tests for User Story 1 ⚠️

- [X] T007 [P] [US1] Escrever `backend/tests/gastos/test_categorias_service.py` (parte padrão):
  - `criar_categorias_padrao(usuario)` cria exatamente Moradia (`azul`), Alimentação (`laranja`), Transporte (`roxo`), Saúde (`vermelho`), Lazer (`rosa`), Educação (`ciano`) e Outros (`cinza`) ([research R-03](research.md));
  - chamada de novo, não duplica (continua com 7);
  - para quem já tem qualquer categoria (ex.: só "Pets"), não cria nada;
  - não mexe nas categorias de outra conta.
- [X] T008 [P] [US1] Escrever `backend/tests/gastos/test_cadastro_categorias.py`:
  - `POST /api/usuarios/` com dados válidos → 201 e a conta nova tem as 7 categorias;
  - se `criar_categorias_padrao` lançar erro (simular com `monkeypatch` no módulo `accounts.services.cadastro`), o cadastro falha e **nenhuma conta** é criada (atômico, [research R-04](research.md)); o erro **não** vira "Já existe uma conta com este e-mail.";
  - e-mail duplicado continua dando 400 com a mensagem da spec 002.
- [X] T009 [P] [US1] Escrever `backend/tests/gastos/test_migration_categorias.py` com `@pytest.mark.django_db(transaction=True)` e `MigrationExecutor` ([research R-05](research.md)): migrar para `("gastos", "0001_initial")`; criar, pelo model histórico, um usuário sem categorias e outro com uma categoria "Pets"; migrar para `("gastos", "0002_categorias_padrao_contas_existentes")`; conferir 7 categorias padrão no primeiro e só "Pets" no segundo. Ao final, migrar de volta para o estado mais recente (`executor.loader.graph.leaf_nodes()`).

  Rodar e confirmar a **falha**.

### Implementation for User Story 1

- [X] T010 [US1] Implementar `backend/gastos/services/__init__.py` e `backend/gastos/services/categorias.py`: `CATEGORIAS_PADRAO` (7 pares nome/cor do R-03) e `criar_categorias_padrao(usuario)`: se `Categoria.objects.do_dono(usuario).exists()`, não faz nada; senão `bulk_create` das 7. Confirmar T007 **verde**
- [X] T011 [US1] Em `backend/accounts/services/cadastro.py`, envolver o cadastro num `transaction.atomic()` externo: dentro dele, um `try` só em volta do `create_user` (o `except IntegrityError` continua virando `EmailJaCadastrado`) e, depois, `criar_categorias_padrao(usuario)`, fora do `try` ([research R-04](research.md)). Trocar o comentário-gancho da spec 002 por uma referência a esta spec. Confirmar T008 **verde** e os testes da spec 002 verdes
- [X] T012 [US1] Criar `backend/gastos/migrations/0002_categorias_padrao_contas_existentes.py` (`RunPython(criar_padrao_para_contas_sem_categorias, RunPython.noop)`), com a lista de nomes e cores **copiada** na migration e `apps.get_model` para `Usuario` e `Categoria` ([research R-05](research.md)). Dependência: `("gastos", "0001_initial")` e a última migration de `accounts`. Confirmar T009 **verde**
- [X] T013 [US1] Subir (`docker compose up -d --wait`) e validar o S2 do [quickstart.md](quickstart.md): toda conta do banco local com 7 categorias; depois de `docker compose restart backend`, continua 7

  > **Resultado (2026-10-07)**: ✅ backend com 184 verdes (175 + 4 do service + 4 do cadastro + 1
  > da migration).
  > - T007 a T009 falharam primeiro (service, chamada no cadastro e migration inexistentes).
  > - T008: o teste de falha nas categorias chama o `cadastrar_usuario` direto (pelo cliente HTTP, a
  >   exceção sobe no próprio teste); confere que nenhuma conta e nenhuma categoria ficam. Acrescentei
  >   o caso de corrida do e-mail: continua virando `EmailJaCadastrado`, sem categorias a mais.
  > - T011: `cadastrar_usuario` virou `@transaction.atomic`; o `try` cobre só o `create_user` (com o
  >   próprio `atomic` interno), e `criar_categorias_padrao` vem depois, fora do `except`.
  > - T013 (S2): as 8 contas do banco local ficaram com 7 categorias cada; depois de outro `restart`
  >   do backend, continuam 56 categorias para 8 donos (sem duplicar).

**Checkpoint**: categorias padrão para todas as contas; suítes verdes.

---

## Phase 4: User Story 2 - Criar e renomear categorias (Priority: P1)

**Goal**: API de listar, criar, abrir e renomear, com nome único por conta sem diferenciar
maiúsculas (FR-003 a FR-006, FR-009).

**Independent Test**: [contracts/api-categorias.md](contracts/api-categorias.md) pela suíte; kit de isolamento verde.

### Tests for User Story 2 ⚠️

- [X] T014 [P] [US2] Escrever `backend/tests/gastos/test_categorias_api.py` com `pytestmark = pytest.mark.django_db` e:
  - `TestIsolamentoCategoria(CasosDeIsolamento)` ([kit da spec 004](../../backend/tests/isolamento.py)): `modelo = Categoria`, `url_lista = "/api/categorias/"`, `payload_criacao = {"nome": "Pets", "cor": "verde"}`, `payload_alteracao = {"nome": "Bichos"}`, e `criar(usuario)` gerando **nomes diferentes a cada chamada** (ex.: `f"Categoria {Categoria.objects.count() + 1}"`), porque o nome é único por conta;
  - `GET` lista em ordem alfabética sem diferenciar maiúsculas, com exatamente as chaves `{"id", "nome", "cor"}`;
  - `POST {"nome": "  Pets  ", "cor": "verde"}` → 201 com `nome == "Pets"`;
  - `POST` com "pets" e com "PETS" depois de "Pets" → 400 `{"nome": ["Já existe uma categoria com este nome."]}`;
  - Bia criar "Pets" com Ana já tendo "Pets" → 201;
  - nome vazio e só espaços → `{"nome": ["Este campo é obrigatório."]}`; 51 caracteres → 400 no campo `nome` (registrar o texto exato do DRF e ajustar o [contrato](contracts/api-categorias.md), ponto de atenção 2 do plano);
  - `PATCH` renomeando "Lazer" para "Lazer e viagens" → 200, cor mantida; `PATCH` de "lazer" para "Lazer" na própria categoria → 200 (mesmo nome, outra grafia);
  - `PATCH` para o nome de outra categoria da mesma conta (sem diferenciar maiúsculas) → 400 com a mensagem de nome repetido.
- [X] T015 [P] [US2] Escrever em `backend/tests/gastos/test_categorias_api.py` o caso de corrida ([research R-06](research.md)): com `monkeypatch` fazendo o `validate_nome` aceitar o nome repetido, o `IntegrityError` da constraint vira 400 `{"nome": ["Já existe uma categoria com este nome."]}` (sem erro 500).

  Rodar e confirmar a **falha** (rota inexistente).

### Implementation for User Story 2

- [X] T016 [US2] Implementar `CategoriaSerializer(RegistroComDonoSerializer)` em `backend/gastos/serializers.py`: `fields = ["id", "nome", "cor", "dono"]`; `nome = CharField(max_length=50, error_messages={"blank": "Este campo é obrigatório."})` (o `trim_whitespace` do DRF tira os espaços das pontas); `validate_nome` recusa nome já usado pela pessoa (`do_dono(request.user).filter(nome__iexact=valor)`, excluindo a própria instância numa edição) com "Já existe uma categoria com este nome."
- [X] T017 [US2] Implementar `CategoriaViewSet(FiltroPorDonoMixin, ModelViewSet)` em `backend/gastos/views.py` (`queryset = Categoria.objects.all()`), com `perform_create` e `perform_update` que convertem `IntegrityError` em `ValidationError({"nome": [...]})`; e `backend/gastos/urls.py` com `DefaultRouter(trailing_slash=True)` registrando `categorias` (`basename="categoria"`). Confirmar T014 e T015 **verdes**, e a guarda de rotas da spec 004 verde

  > **Resultado (2026-10-07)**: ✅ backend com 206 verdes (184 + 8 do kit de isolamento + 14 da API).
  > - T014 e T015 falharam primeiro (`gastos.serializers` inexistente).
  > - Texto do limite de 50 caracteres confirmado: "Certifique-se de que este campo não tenha mais
  >   de 50 caracteres." (igual ao contrato; ponto de atenção 2 resolvido).
  > - A docstring do kit (`tests/isolamento.py`) passou a gerar nomes únicos no exemplo (achado I2).
  > - **Guarda de proteção da spec 003 corrigida**: ela só lia `view_class`, e as rotas de viewset
  >   expõem a classe em `cls`; acusou as rotas de categorias como desprotegidas. Agora lê `cls`
  >   ou `view_class`, como a guarda de isolamento da spec 004.
  > - Router trocado para `SimpleRouter`: o `DefaultRouter` criaria uma página raiz em `/api/`
  >   listando as rotas, e o README promete 404 nesse endereço. Conferido: `/api/` → 404,
  >   `/api/categorias/` sem sessão → 401.
  > - O `perform_create`/`perform_update` salvam dentro de `transaction.atomic()`, para o
  >   `IntegrityError` da corrida não invalidar a transação antes de virar o 400.

**Checkpoint**: API de categorias com isolamento comprovado; suítes verdes.

---

## Phase 5: User Story 3 - Escolher a cor de cada categoria (Priority: P2)

**Goal**: paleta pela API, cor automática e recusa de cor fora da paleta (FR-007).

**Independent Test**: quickstart S7.

### Tests for User Story 3 ⚠️

- [X] T018 [P] [US3] Acrescentar a `backend/tests/gastos/test_categorias_service.py`: `escolher_cor_livre(usuario)` devolve a primeira cor da paleta que a pessoa não usa (com "azul" e "laranja" em uso → "roxo"); com as 12 em uso, devolve `PALETA[quantidade % 12].codigo` ([research R-07](research.md)); cores de outra conta não contam.
- [X] T019 [P] [US3] Acrescentar a `backend/tests/gastos/test_categorias_api.py`:
  - `GET /api/categorias/cores/` → 200 com as 12 cores `{"codigo", "nome", "hex"}` na ordem do R-02; sem sessão → 401;
  - `POST` sem `cor` → 201 com a primeira cor livre da pessoa;
  - `POST` e `PATCH` com `"cor": "dourado"` → 400 `{"cor": ["Escolha uma das cores disponíveis."]}`, e a cor anterior fica;
  - `PATCH {"cor": "indigo"}` → 200, nome mantido.

  Rodar e confirmar a **falha**.

### Implementation for User Story 3

- [X] T020 [US3] Acrescentar `escolher_cor_livre(usuario)` a `backend/gastos/services/categorias.py`. Confirmar T018 **verde**
- [X] T021 [US3] No `CategoriaSerializer`: `cor = ChoiceField(choices=CHOICES, required=False, error_messages={"invalid_choice": "Escolha uma das cores disponíveis."})`; na criação sem `cor`, usar `escolher_cor_livre(request.user)` (no `create` do serializer). No `CategoriaViewSet`, `@action(detail=False) cores` devolvendo `[{"codigo", "nome", "hex"}]` da `PALETA`. Confirmar T019 **verde**

  > **Resultado (2026-10-07)**: ✅ backend com 216 verdes (206 + 4 do service + 6 da API).
  > - T018 e T019 falharam primeiro (`escolher_cor_livre` inexistente).
  > - Acrescentei o caso "sem categorias, a cor livre é a primeira" (azul) e o de troca de cor
  >   mantendo o nome.
  > - A cor automática entra no `create` do serializer (depois da validação, com o dono já
  >   preenchido pela sessão); `PATCH` sem `cor` mantém a cor atual.

**Checkpoint**: paleta e cores funcionando na API; suítes verdes.

---

## Phase 6: User Story 4 - Excluir categorias (Priority: P2)

**Goal**: exclusão livre da própria categoria; a regra do destino é da US-07 (FR-008).

**Independent Test**: suíte da API.

### Tests for User Story 4 ⚠️

- [X] T022 [US4] Acrescentar a `backend/tests/gastos/test_categorias_api.py`: `DELETE` da própria categoria → 204 e ela some da lista; excluir todas as categorias → lista `[]`, e as padrão **não** voltam ao listar de novo; `DELETE` de categoria da Bia → 404 e ela continua existindo (já coberto pelo kit; conferir).

  Nota: hoje `criar_categorias_padrao` cria para quem não tem nenhuma categoria; ela só é chamada no cadastro e na migration (uma vez por banco), então uma conta que excluiu tudo não recebe as padrão de novo. O teste confere a listagem depois de excluir tudo.

  Rodar e registrar: é esperado que **passe de primeira** (o `ModelViewSet` já tem `destroy`); nesse caso, registrar.
- [X] T023 [US4] Se a T022 falhar em algum ponto, corrigir em `backend/gastos/views.py`. Rodar a suíte

  > **Resultado (2026-10-07)**: ✅ backend com 219 verdes (216 + 3).
  > - Os 3 testes **passaram de primeira**, como previsto: o `ModelViewSet` já tem `destroy`. Prova da
  >   falha: com `DELETE` fora do `http_method_names` da viewset, **5** testes de exclusão falharam
  >   (os 3 novos e 2 do kit de isolamento). Código restaurado (`git diff` vazio).
  > - O teste "excluir todas" usa uma conta criada pelo cadastro real (com as 7 padrão) e confere
  >   que, depois de excluir todas, a lista continua vazia.
  > - T023 sem mudança de código.

**Checkpoint**: exclusão coberta por testes; suítes verdes.

---

## Phase 7: User Story 5 - Gerenciar categorias pela tela (Priority: P1)

**Goal**: tela `/categorias` com lista, criação, edição na linha, seletor de cor e exclusão com
confirmação (FR-011 a FR-014; [contrato da tela](contracts/tela-categorias.md)).

**Independent Test**: quickstart S3, S4 e S6.

### Tests for User Story 5 ⚠️

- [X] T024 [P] [US5] Escrever `frontend/src/components/SeletorCor.test.jsx`: com a paleta recebida por prop, mostra um `group` com nome "Cor" e um rádio por cor com o nome acessível (ex.: "Verde"); clicar marca a cor e chama `aoMudar("verde")`; com `valor="azul"`, o rádio "Azul" vem marcado; navegação por setas muda a seleção (rádio nativo).
- [X] T025 [P] [US5] Escrever `frontend/src/pages/Categorias/Categorias.test.jsx` (com `renderizarComRotas`, sessão gravada e `simularApi` para `/usuarios/eu/`, `/categorias/cores/` e `/categorias/`):
  - mostra "Carregando categorias…" e depois a lista na ordem da API, com amostra de cor e nome;
  - lista vazia → "Nenhuma categoria. Crie a primeira acima.";
  - criar: digitar "Pets", escolher "Verde", "Adicionar" → `POST` com `{"nome": "Pets", "cor": "verde"}`, recarrega a lista e limpa o formulário; o botão mostra "Adicionando…" e fica desabilitado durante o envio;
  - criar com 400 `{"nome": ["Já existe uma categoria com este nome."]}` → mensagem ligada ao campo "Nome" (`aria-describedby`), texto mantido;
  - editar: "Editar Saúde" troca a linha por campo e seletor; mudar o nome e "Salvar" → `PATCH` e lista recarregada; "Cancelar" volta sem chamar a API;
  - excluir: com `window.confirm` simulado devolvendo `false`, não chama a API; com `true`, chama `DELETE` e recarrega; o texto da confirmação é `Excluir a categoria "Saúde"?`;
  - falha de rede ao carregar → "Não foi possível falar com o servidor. Tente novamente.".
- [X] T026 [P] [US5] Acrescentar a `frontend/src/components/Layout.test.jsx`: o menu tem "Categorias" com `href="/categorias"`, depois de "Início".

  Rodar e confirmar a **falha**.

### Implementation for User Story 5

- [X] T027 [P] [US5] Criar `frontend/src/api/categorias.js` com `listarCategorias()`, `listarCores()`, `criarCategoria(dados)`, `atualizarCategoria(id, dados)` (PATCH) e `excluirCategoria(id)`, todas via `requisitarAutenticada`, com `Content-Type: application/json` quando houver corpo
- [X] T028 [P] [US5] Criar `frontend/src/components/SeletorCor.jsx` ([research R-09](research.md)): `fieldset` com `legend` "Cor", rádios com `name` único por instância (`useId`), rótulo com o nome da cor e amostra (`span` com `background` do `hex`, `aria-hidden`). Confirmar T024 **verde**
- [X] T029 [US5] Criar `frontend/src/hooks/useCategorias.js`: carrega categorias e cores juntas; expõe `{ categorias, cores, carregando, erroCarregar, criar, atualizar, excluir }`, cada ação devolvendo `{ok: true}` ou `{ok: false, erro}` (com `interpretarErro`) e recarregando a lista no sucesso
- [X] T030 [US5] Criar `frontend/src/pages/Categorias/Categorias.jsx` conforme o [contrato da tela](contracts/tela-categorias.md), reaproveitando `CampoTexto`, `AvisoFormulario` e `SeletorCor`; botões com nome acessível incluindo a categoria ("Editar Saúde", "Excluir Saúde"); confirmação com `window.confirm`
- [X] T031 [US5] Em `frontend/src/App.jsx`, rota `/categorias` como filha do `Layout`; em `frontend/src/components/Layout.jsx`, `NavLink` "Categorias" depois de "Início"; em `frontend/src/estilos.css`, estilos da lista, das amostras de cor, do seletor (amostras que quebram linha) e da edição na linha, sem rolagem horizontal em 360 px. Confirmar T025 e T026 **verdes**
- [X] T032 [US5] Validar no navegador S3, S4 (com o tempo, SC-004) e S6 do [quickstart.md](quickstart.md)

  > **Resultado (2026-10-07)**: ✅ interface com 85 testes verdes (69 + 5 do seletor + 10 da tela + 1
  > do menu), estáveis em três rodadas seguidas; backend 219.
  > - T024 a T026 falharam primeiro (componentes inexistentes; menu sem "Categorias").
  > - Na tela, a cor de cada linha também vai em texto oculto ("Cor: Vermelho") para leitores de
  >   tela; a amostra visual é `aria-hidden`.
  > - Navegador, conta nova `teste.s3cat@exemplo.com` criada pelo cadastro:
  >   - **S3** ✅ as 7 padrão em ordem (Alimentação, Educação, Lazer, Moradia, Outros, Saúde,
  >     Transporte), cada uma com a cor do R-03;
  >   - **S4** ✅ "Pets" verde criada na posição certa e o formulário limpo; "pets" recusado com
  >     "Já existe uma categoria com este nome." no campo e o texto mantido; "Assinaturas" sem cor →
  >     amarelo (primeira livre); "Lazer" → "Lazer e viagens" mantendo rosa; "Saúde" → Índigo;
  >     excluir "Pets": confirmação `Excluir a categoria "Pets"?`, cancelar mantém, confirmar exclui
  >     (o `window.confirm` foi substituído por um simulado, porque o diálogo nativo trava a
  >     automação). Do início ao fim, **46 s** (SC-004: até 2 min);
  >   - **S6** ✅ em 360 px, sem rolagem horizontal (lista e edição na linha); "Academia" criada só
  >     pelo teclado (Tab até as cores, setas até "Roxo", Enter).

**Checkpoint**: categorias gerenciáveis pela tela; suítes verdes.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T033 [P] Atualizar o `README.md`: "Estado atual" (categorias pela tela) e, na seção 3, a tela `/categorias` e as rotas `/api/categorias/` e `/api/categorias/cores/`, com link para o [contrato da API](contracts/api-categorias.md)
- [X] T034 Executar o [quickstart.md](quickstart.md) completo (S1 a S7) e registrar o resultado

  > **Resultado (2026-10-07)**: ✅
  > - S1: `sh testar.sh` → backend 219 e interface 85, "Backend e interface: todos os testes passaram.";
  > - S2: todas as 9 contas do banco local com categorias (8 com as 7 padrão; `teste.s3cat` com 9,
  >   por causa do S4 da T032); `makemigrations --check` sem pendências;
  > - S3, S4 e S6: validados na T032 (S4 em 46 s);
  > - S5: com a sessão de Ana, `GET /api/categorias/<id de categoria da Bia>/` → `404 {"detail":
  >   "Não encontrado."}`;
  > - S7: `/api/categorias/cores/` com 12 cores (de Azul a Índigo); `"cor": "dourado"` → `400
  >   {"cor": ["Escolha uma das cores disponíveis."]}`.
- [X] T035 Fechar a Definition of Done:
  - suítes verdes e todas as tarefas marcadas; `makemigrations --check` sem pendências;
  - em `BACKLOG.md`, na US-05, marcar ☑ os 3 primeiros critérios (padrão no cadastro e para contas antigas; criar, renomear e excluir com nome único; cor) e anotar o 4º ("categoria com gastos vinculados...") como coberto pela US-07 (Clarifications Q2); na US-01, marcar ☑ "Ao criar a conta, as categorias padrão são geradas", com nota "spec 006".

  > **Resultado (2026-10-07)**: ✅ backend 219 e interface 85 verdes; 35/35 tarefas marcadas.
  > - US-05: 3 critérios ☑; o 4º (excluir com gastos vinculados) anotado como coberto pela US-07, e
  >   a própria US-07 ganhou esse critério, "herdado da US-05", para não se perder.
  > - US-01: "categorias padrão no cadastro" ☑, e a US-01 fica completa.
  > - README: estado atual, tela e rotas de categorias, nota sobre as categorias padrão.

**Checkpoint**: feature pronta para PR na `main`.

---

## Dependencies & Execution Order

```text
Setup → Foundational → US1 → US2 → US3 → US4 → US5 → Polish
```

- **Foundational** (paleta e model) bloqueia tudo.
- **US1** usa só o model; **US2** cria a API; **US3** estende o serializer e a viewset da US2;
  **US4** depende da API (US2). **US5** depende da API completa (US2 a US4).
- `backend/gastos/serializers.py`, `views.py`, `services/categorias.py`,
  `tests/gastos/test_categorias_api.py` e `test_categorias_service.py` são editados por várias
  fases, sempre em sequência.

### Parallel Opportunities

- Foundational: T003 ∥ T004.
- US1: T007 ∥ T008 ∥ T009.
- US2: T014 ∥ T015 (mesmo arquivo: escrever em sequência, rodar juntos).
- US3: T018 ∥ T019.
- US5: T024 ∥ T025 ∥ T026; T027 ∥ T028.

## Parallel Example: User Story 1

```bash
Task: "T007 Testes do service de categorias padrão em backend/tests/gastos/test_categorias_service.py"
Task: "T008 Testes do cadastro com categorias em backend/tests/gastos/test_cadastro_categorias.py"
Task: "T009 Teste da migration de dados em backend/tests/gastos/test_migration_categorias.py"
```

## Implementation Strategy

### MVP First

Setup + Foundational + US1 + US2 + US5 (com a cor automática da US3): categorias padrão para todos,
criar e renomear pela tela. A US-07 (gastos) já pode começar depois da US1 e da US2.

### Incremental Delivery

Um checkpoint por fase, com `sh testar.sh` verde.

## Notes

- **Kit de isolamento com nome único**: o `criar(usuario)` da subclasse precisa gerar nomes
  diferentes, senão o próprio kit esbarra na constraint (T014).
- **Teste da migration** (`transaction=True`) é mais lento; é um teste só.
- **Sem rebuild**: nenhuma dependência nova; backend e `frontend/src` são montados.
- Commits em pt-BR, Conventional Commits, **sem** `Co-Authored-By` nem rodapés de IA; push a cada
  commit (constituição v1.2.0).

**Commit recomendado após cada checkpoint (T002, T006, T013, T017, T021, T023, T032, T035)**:

| Checkpoint | Mensagem sugerida |
|---|---|
| T002 | `chore: cria o app gastos` |
| T006 | `feat: adiciona categoria com paleta de cores e nome único por conta` |
| T013 | `feat: cria as categorias padrão no cadastro e para contas existentes (US1)` |
| T017 | `feat: adiciona API para criar e renomear categorias (US2)` |
| T021 | `feat: adiciona paleta de cores e cor automática às categorias (US3)` |
| T023 | `test: cobre a exclusão de categorias (US4)` |
| T032 | `feat: adiciona tela de categorias (US5)` |
| T035 | `docs: documenta as categorias e conclui US-05` |

O primeiro commit (T002) também inclui os artefatos da spec (`specs/006-categorias-gasto/`).
