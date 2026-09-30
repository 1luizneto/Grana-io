---

description: "Lista de tarefas da feature 002-cadastro-usuario (US-01 + hash de senha do RNF-02)"
---

# Tasks: Cadastro de Usuário

**Input**: documentos de design em `/specs/002-cadastro-usuario/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: **obrigatórios** pelo Princípio IV da constituição. O model/manager, o validador de
senha, o service de cadastro e o endpoint são core. Escreva os testes primeiro e confirme que
falham antes de implementar. Settings, compose e `.env.example` são glue e ficam validados pelo
[quickstart.md](quickstart.md).

**Organization**: cada fase termina num **Checkpoint**. No checkpoint, pare com a suíte verde,
apresente o resumo das mudanças e sugira a mensagem de commit. O commit é manual, sem trailers
de IA.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: US1 (criar conta), US2 (e-mail duplicado), US3 (validação dos dados)
- Caminhos relativos à raiz do repositório. Suíte: `docker compose run --rm backend pytest`

---

## Phase 1: Setup

**Purpose**: esqueleto do app `accounts`

- [ ] T001 [P] Criar o app `accounts`: `backend/accounts/__init__.py`, `backend/accounts/apps.py` (`AccountsConfig`, `name = "accounts"`, `default_auto_field = "django.db.models.BigAutoField"`), `backend/accounts/migrations/__init__.py`, `backend/accounts/services/__init__.py` e `backend/accounts/urls.py` com `urlpatterns = []`
- [ ] T002 [P] Criar o pacote de testes `backend/tests/accounts/__init__.py`
- [ ] T003 Em `backend/config/settings.py`, adicionar `"accounts"` a `INSTALLED_APPS` (depois de `"corsheaders"`, antes de `"core"`). Em `backend/config/urls.py`, adicionar `path("api/", include("accounts.urls"))` ao lado da rota do `core`. Rodar a suíte e confirmar que continua verde (34) (depende de T001)

**Checkpoint**: app registrado, suíte verde.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: modelo de usuário próprio (`AUTH_USER_MODEL`), necessário para todas as histórias.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase. O `AUTH_USER_MODEL` precisa estar definido **antes** de gerar a migration ([research R-01, R-02](research.md)).

- [ ] T004 Escrever **primeiro** os testes do model e do manager em `backend/tests/accounts/test_models.py` (`@pytest.mark.django_db`). Casos:
  - `get_user_model()` é `accounts.Usuario`, e `USERNAME_FIELD == "email"`;
  - `Usuario.objects.create_user(email=" Ana@Exemplo.COM ", nome="  Ana  ", password="uma-senha-boa-2026")` grava `email == "ana@exemplo.com"` e `nome == "Ana"`;
  - `password` começa com `"pbkdf2_sha256$"`, `check_password("uma-senha-boa-2026")` é `True` e o texto da senha não aparece em `password`;
  - `is_active is True`, `is_staff is False` e `is_superuser is False`;
  - `criado_em` fica preenchido;
  - `str(usuario) == "ana@exemplo.com"`;
  - `create_superuser(...)` cria com `is_staff` e `is_superuser` verdadeiros;
  - `save()` de um `Usuario` com e-mail `"X@Y.com"` grava `"x@y.com"`.

  Rodar a suíte e confirmar a **falha** (data-model, "Usuario").
- [ ] T005 Implementar `Usuario(AbstractBaseUser, PermissionsMixin)` e `UsuarioManager(BaseUserManager)` em `backend/accounts/models.py`, conforme [data-model.md](data-model.md):
  - Campos:
    - `email = EmailField(max_length=254, unique=True)`;
    - `nome = CharField(max_length=150)`;
    - `is_active = BooleanField(default=True)`;
    - `is_staff = BooleanField(default=False)`;
    - `criado_em = DateTimeField(auto_now_add=True)`.
  - Configuração:
    - `USERNAME_FIELD = "email"`, `EMAIL_FIELD = "email"`, `REQUIRED_FIELDS = ["nome"]`;
    - `@staticmethod normalizar_email(valor)`, que devolve `valor.strip().lower()`;
    - `save()` normaliza o e-mail e faz `strip` no nome;
    - `__str__` devolve o e-mail.
  - Manager:
    - `create_user(email, nome, password=None, **extra)` força `is_staff=False` e `is_superuser=False` e chama `set_password`;
    - `create_superuser` usa `is_staff=True` e `is_superuser=True`;
    - `get_by_natural_key` normaliza o e-mail recebido.
- [ ] T006 Definir `AUTH_USER_MODEL = "accounts.Usuario"` em `backend/config/settings.py`. Gerar a migration dentro do container com `docker compose run --rm backend python manage.py makemigrations accounts` e conferir que `backend/accounts/migrations/0001_initial.py` foi criado com LF (depende de T005)
- [ ] T007 **Recriar o banco de desenvolvimento** ([research R-02](research.md)). É uma ação destrutiva, então **pedir confirmação ao responsável antes**. Rodar `docker compose down -v` e depois `docker compose up -d --wait`, e conferir nos logs do backend que `accounts.0001_initial` foi aplicada e que a tabela `auth_user` não existe (`docker compose exec -T db psql -U grana -d grana -c "\dt"`)
- [ ] T008 Rodar a suíte e confirmar T004 **verde** e a guarda `tests/test_migrations.py` verde. Validar o quickstart Q9: `createsuperuser` pede e-mail e nome

**Checkpoint**: `Usuario` é o modelo de usuário do projeto, com banco recriado limpo e suíte verde.

---

## Phase 3: User Story 1 - Criar uma conta (Priority: P1) 🎯 MVP

**Goal**: `POST /api/usuarios/` cria uma conta ativa, sem privilégios, com senha protegida; responde só `nome` e `email`, sem autenticar; pode ser fechado por configuração.

**Independent Test**: quickstart Q1, Q2, Q5, Q6 e Q7.

### Tests for User Story 1 ⚠️

> Escreva estes testes primeiro e confirme que falham antes de implementar.

- [ ] T009 [P] [US1] Escrever `backend/tests/accounts/test_cadastro_service.py` (`@pytest.mark.django_db`). Casos:
  - `cadastrar_usuario(nome="Ana", email="Ana@Exemplo.com", senha="uma-senha-boa-2026")` devolve um `Usuario` persistido, com e-mail normalizado e senha verificável por `check_password`;
  - **atomicidade**: fazer `monkeypatch` em `Usuario.objects.create_user` com um wrapper que chama o original (gravando o usuário) e **depois** lança `RuntimeError`. `cadastrar_usuario` propaga o erro, e ao final `Usuario.objects.count() == 0`, o que prova o `transaction.atomic()` sem criar código especulativo no service;
  - `cadastro_aberto()` segue `settings.CADASTRO_ABERTO` (com `override_settings`).
- [ ] T010 [P] [US1] Escrever `backend/tests/accounts/test_cadastro_api.py`, usando `APIClient` sem autenticação, conforme [contracts/api-cadastro.md](contracts/api-cadastro.md). Casos:
  - `POST /api/usuarios/` válido, com e-mail `" Ana@Exemplo.com "` e nome `"  Ana Souza "`, retorna 201 e o corpo **exatamente** `{"nome": "Ana Souza", "email": "ana@exemplo.com"}`, sem `id`, `senha`, `token`, `access` ou `refresh`;
  - o usuário existe com `is_active=True`, `is_staff=False` e `is_superuser=False`;
  - o texto da senha não aparece no corpo da resposta;
  - `GET`, `PUT`, `PATCH` e `DELETE` retornam 405;
  - com `override_settings(CADASTRO_ABERTO=False)`, um cadastro **válido** retorna 403 com `{"detail": "O cadastro de novas contas está desativado neste sistema."}` e nenhum usuário é criado;
  - a view de cadastro marca `senha` e `confirmacao_senha` como parâmetros sensíveis. Montar o `POST` com `RequestFactory().post("/api/usuarios/", data=..., content_type=...)`, com dados de formulário para preencher `request.POST`, e chamar `CadastroView.as_view()(request)`. Depois verificar que `SafeExceptionReporterFilter().get_post_parameters(request)` devolve `senha` e `confirmacao_senha` como `"********************"` e mantém `nome` legível. É o mesmo filtro que o Django usa na página de erro.

  Rodar a suíte e confirmar a **falha**.

### Implementation for User Story 1

- [ ] T011 [US1] Implementar `backend/accounts/services/cadastro.py`:
  - `cadastro_aberto() -> bool` lê `settings.CADASTRO_ABERTO`;
  - `cadastrar_usuario(nome, email, senha) -> Usuario` roda em `transaction.atomic()` e chama `Usuario.objects.create_user(email=email, nome=nome, password=senha)`.

  Deixar um comentário no ponto onde a US-05 acrescentará as categorias padrão, com chamada explícita e sem signals ([research R-09](research.md)).

  Na mesma tarefa, adicionar em `backend/config/settings.py` a configuração `CADASTRO_ABERTO = env_bool("GRANA_CADASTRO_ABERTO", True)`. Sem ela, `cadastro_aberto()` dá `AttributeError` e a T014 não consegue ficar verde.
- [ ] T012 [US1] Implementar em `backend/accounts/serializers.py`:
  - `CadastroSerializer(serializers.Serializer)` com os campos:
    - `nome = CharField(max_length=150)`;
    - `email = EmailField(max_length=254)`, com `validate_email` que devolve `Usuario.normalizar_email(valor)`;
    - `senha = CharField(max_length=128, write_only=True, trim_whitespace=False)`;
    - `confirmacao_senha = CharField(write_only=True, trim_whitespace=False)`.
  - `UsuarioCadastradoSerializer(serializers.ModelSerializer)`, só com `fields = ["nome", "email"]`.

  As regras completas de senha, confirmação e duplicidade entram na US2 e na US3.
- [ ] T013 [US1] Implementar `CadastroView(APIView)` em `backend/accounts/views.py`:
  - `permission_classes = [AllowAny]`, `authentication_classes = []`, `http_method_names = ["post", "options"]`;
  - `@method_decorator(sensitive_post_parameters("senha", "confirmacao_senha"), name="dispatch")`;
  - `post()` faz, em ordem:
    1. se `not cadastro_aberto()`, devolve 403 com a mensagem do contrato;
    2. valida com `CadastroSerializer` (`raise_exception=True`);
    3. chama `cadastrar_usuario(**dados sem confirmacao_senha)`;
    4. devolve 201 com `UsuarioCadastradoSerializer(usuario).data`.
- [ ] T014 [US1] Registrar `path("usuarios/", CadastroView.as_view(), name="cadastro")` em `backend/accounts/urls.py`. Rodar a suíte e confirmar T009 e T010 **verdes**
- [ ] T015 [US1] Expor a configuração já criada na T011 (`CADASTRO_ABERTO` no settings). Adicionar `GRANA_CADASTRO_ABERTO: ${GRANA_CADASTRO_ABERTO:-1}` ao `environment` do `backend` em `compose.yaml`. Acrescentar ao `.env.example` a variável `GRANA_CADASTRO_ABERTO=1`, com o comentário "1 = qualquer pessoa na rede pode criar conta; 0 = cadastro desativado (403), contas existentes continuam funcionando" (FR-012, [research R-07](research.md))
- [ ] T016 [US1] Validar pelo [quickstart.md](quickstart.md) os cenários Q1, Q2, Q5, Q6 e Q7. Registrar o resultado no checkpoint

**Checkpoint**: cadastro funcional e demonstrável; suíte verde.

---

## Phase 4: User Story 2 - Rejeitar e-mail já cadastrado (Priority: P1)

**Goal**: e-mail duplicado (qualquer caixa/espaços, inclusive concorrente) recusado com "Já existe uma conta com este e-mail."; nunca 2 contas por e-mail.

**Independent Test**: quickstart Q3 + testes de corrida.

### Tests for User Story 2 ⚠️

- [ ] T017 [P] [US2] Adicionar a `backend/tests/accounts/test_cadastro_api.py`:
  - com `ana@exemplo.com` já cadastrado, os cadastros com `"ana@exemplo.com"`, `"ANA@Exemplo.com"` e `"  ana@exemplo.com  "` retornam 400 com `{"email": ["Já existe uma conta com este e-mail."]}`;
  - `Usuario.objects.filter(email="ana@exemplo.com").count() == 1`.
- [ ] T018 [P] [US2] Adicionar a `backend/tests/accounts/test_cadastro_service.py` a **corrida simulada**: com o e-mail já gravado diretamente no banco (sem passar pelo serializer), `cadastrar_usuario` com o mesmo e-mail lança `EmailJaCadastrado`, e continua existindo 1 conta. Adicionar a `test_cadastro_api.py` o caso em que `accounts.serializers` não detecta o duplicado (`monkeypatch` na checagem) e a view mesmo assim responde 400 com a mensagem de duplicado, e não 500. Rodar a suíte e confirmar a **falha** de T017 e T018

### Implementation for User Story 2

- [ ] T019 [US2] Em `backend/accounts/serializers.py`, fazer o `validate_email` levantar `ValidationError("Já existe uma conta com este e-mail.")` quando `Usuario.objects.filter(email=normalizado).exists()` ([research R-03](research.md))
- [ ] T020 [US2] Em `backend/accounts/services/cadastro.py`, definir `class EmailJaCadastrado(Exception)` e, em `cadastrar_usuario`, capturar `IntegrityError` e relançar como `EmailJaCadastrado`. Em `backend/accounts/views.py`, converter `EmailJaCadastrado` em 400 `{"email": ["Já existe uma conta com este e-mail."]}`. Rodar a suíte e confirmar T017 e T018 **verdes**
- [ ] T021 [US2] Validar o cenário Q3 do [quickstart.md](quickstart.md)

**Checkpoint**: unicidade do e-mail garantida, inclusive sob concorrência; suíte verde.

---

## Phase 5: User Story 3 - Validar os dados informados (Priority: P1)

**Goal**: todo dado ausente/inválido é recusado com mensagens pt-BR por campo, todas de uma vez, sem criar conta.

**Independent Test**: quickstart Q4.

### Tests for User Story 3 ⚠️

- [ ] T022 [P] [US3] Escrever `backend/tests/accounts/test_validators.py` para o `SenhaComumPtBrValidator`:
  - recusa `mudar123`, `brasil123` e `corinthians` com a mensagem "Esta senha é muito comum.";
  - a comparação ignora maiúsculas (`Brasil123` também é recusada);
  - aceita `uma-senha-boa-2026`;
  - `get_help_text()` devolve um texto em pt-BR.
- [ ] T023 [P] [US3] Adicionar a `backend/tests/accounts/test_cadastro_api.py` um teste parametrizado, com 400 e **nenhum usuário criado** em cada caso:
  - `{}` → os 4 campos com "Este campo é obrigatório.";
  - `nome` = `"   "` → `nome`: "Este campo é obrigatório.";
  - nome com 151 caracteres → erro em `nome`;
  - `email` = `"ana@"` e `"ana.exemplo.com"` → `email`: "Insira um endereço de email válido.";
  - e-mail com mais de 254 caracteres → erro em `email`;
  - senha e confirmação diferentes → `confirmacao_senha`: "As senhas não conferem.";
  - senha `"abc12"` → mensagem de `senha` contendo "8 caracteres";
  - senha `"98765432109"` → `senha` contém "Esta senha é inteiramente numérica.";
  - senhas `"senha123"` e `"mudar123"` → `senha` contém "Esta senha é muito comum.";
  - nome `"Carlos Mendes"`, e-mail `"carlos.mendes@exemplo.com"`, senha `"carlosmendes"` → erro de semelhança em `senha`;
  - senha com 129 caracteres → erro em `senha`;
  - vários problemas juntos: nome `"   "`, e-mail `"ana@"`, senha `"123"` e confirmação `"456"` → a mesma resposta traz `nome`, `email`, `senha` (curta e numérica) e `confirmacao_senha`.

  Casos de sucesso adicionais:
  - a senha `"  espaços contam  "`, com confirmação igual, é aceita e fica gravada sem corte (`check_password` com os espaços);
  - o nome `"João D'Ávila"` é aceito.

  Rodar a suíte e confirmar a **falha**.

### Implementation for User Story 3

- [ ] T024 [US3] Implementar `SenhaComumPtBrValidator` em `backend/accounts/validators.py`:
  - conjunto `SENHAS_COMUNS_PTBR`, em minúsculas, com ao menos: `mudar123`, `brasil123`, `corinthians`, `palmeiras`, `saopaulo`, `vasco123`, `gremio123`, `cruzeiro`, `amor1234`, `familia123`, `jesus123`, `deus1234`, `senhasenha`, `abcd1234`, `qwerty123`;
  - `validate(password, user=None)` compara `password.lower()` e levanta `ValidationError("Esta senha é muito comum.", code="password_too_common")`;
  - `get_help_text()` devolve "Sua senha não pode ser uma senha comumente utilizada.".

  ([research R-04](research.md))
- [ ] T025 [US3] Em `backend/config/settings.py`, definir `AUTH_PASSWORD_VALIDATORS` com:
  - `UserAttributeSimilarityValidator` (`OPTIONS: {"user_attributes": ("nome", "email")}`);
  - `MinimumLengthValidator` (`OPTIONS: {"min_length": 8}`);
  - `CommonPasswordValidator`;
  - `NumericPasswordValidator`;
  - `accounts.validators.SenhaComumPtBrValidator`.
- [ ] T026 [US3] Completar o `CadastroSerializer` em `backend/accounts/serializers.py`:
  - `nome` com `error_messages={"blank": "Este campo é obrigatório."}`;
  - **todas as regras no nível de campo, nenhuma no `validate()`**. Verificado no DRF 3.18.1: o
    `validate()` não roda quando algum campo tem erro, e as mensagens de senha sumiriam, violando o
    FR-008 ([research R-10](research.md)):
    - `validate_senha(valor)` chama `django.contrib.auth.password_validation.validate_password(valor, user=Usuario(nome=..., email=...))`, com nome e e-mail vindos de `self.initial_data` (strings, com `strip`, e o e-mail normalizado; vazio se ausente), num usuário não salvo para o validador de semelhança. Converte a `ValidationError` do Django em `serializers.ValidationError(list(e.messages))`;
    - `validate_confirmacao_senha(valor)`: se `valor != self.initial_data.get("senha")`, gera "As senhas não conferem.".

  Rodar a suíte e confirmar T022 e T023 **verdes**, incluindo o caso "vários problemas juntos" com nome vazio **e** senha fraca **e** confirmação diferente na mesma resposta.
- [ ] T027 [US3] Validar o cenário Q4 do [quickstart.md](quickstart.md)

**Checkpoint**: todas as validações da US3 com mensagens pt-BR; suíte verde.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T028 [P] Atualizar `README.md`:
  - na seção 3 (Acessar), acrescentar a rota `POST /api/usuarios/` com um exemplo de requisição e link para [contracts/api-cadastro.md](contracts/api-cadastro.md);
  - na seção 7 (Configuração), explicar `GRANA_CADASTRO_ABERTO`;
  - acrescentar uma subseção "Criar administrador" com `docker compose exec backend python manage.py createsuperuser`.
- [ ] T029 [P] Atualizar `specs/001-infra-docker/contracts/environment.md`: acrescentar `GRANA_CADASTRO_ABERTO` à tabela "Configuráveis" (padrão `1`), com referência a esta spec
- [ ] T030 Executar o [quickstart.md](quickstart.md) completo (Q1 a Q9). Conferir que `makemigrations --check` não acusa nada pendente e que `docker compose logs backend` não contém nenhuma senha usada nos testes manuais (SC-003)
- [ ] T031 Fechar a Definition of Done:
  - suíte verde;
  - todas as tarefas marcadas;
  - em `BACKLOG.md`, marcar ☑ os 4 critérios da US-01 atendidos (o 5º, das categorias, está anotado como movido para a US-05) e o critério do RNF-02 "Senhas são armazenadas com hash (padrão do Django)".

**Checkpoint**: feature pronta para PR na `main`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)** → **Foundational (2)**: bloqueia tudo. É onde entra o `AUTH_USER_MODEL` e o banco é recriado.
- **US1 (3)**: depende da fase 2. É o MVP.
- **US2 (4)** e **US3 (5)**: dependem da US1, porque endurecem o mesmo serializer, service e view. Podem ser feitas em qualquer ordem, mas **não em paralelo**, já que editam `serializers.py`.
- **Polish (6)**: depende de todas.

```text
Setup → Foundational → US1 → US2 → US3 → Polish
                          (US2 e US3 são independentes entre si, mas mexem nos mesmos arquivos)
```

### Within Each User Story

- Testes escritos e **falhando** antes do código (Princípio IV).
- Service → serializer → view → rota.
- `backend/accounts/serializers.py`, `backend/accounts/views.py`, `backend/accounts/services/cadastro.py`
  e `backend/config/settings.py` são editados por várias fases, sempre em sequência.

### Parallel Opportunities

- Setup: T001 ∥ T002.
- US1: T009 ∥ T010 (arquivos de teste distintos).
- US2: T017 ∥ T018.
- US3: T022 ∥ T023. T024 (validador) pode ser feito antes de T025 e T026.
- Polish: T028 ∥ T029.

---

## Parallel Example: User Story 1

```bash
Task: "T009 Testes do service em backend/tests/accounts/test_cadastro_service.py"
Task: "T010 Testes da API em backend/tests/accounts/test_cadastro_api.py"
```

---

## Implementation Strategy

### MVP First

1. Setup + Foundational: `Usuario` como `AUTH_USER_MODEL`, com o banco recriado.
2. US1: cadastro funcionando e fechável.
3. **Parar e validar**: quickstart Q1, Q2, Q5, Q6 e Q7.

### Incremental Delivery

1. US2: unicidade robusta.
2. US3: validações completas.
3. Polish: README, contratos e BACKLOG.

---

## Notes

- **T007 apaga o banco local.** Só há dados de teste, mas a ação precisa de confirmação explícita do responsável no momento da execução.
- Mensagens nativas do Django/DRF são testadas pelo campo + trecho essencial; mensagens próprias, pelo texto exato ([research R-10](research.md)).
- Commits manuais, pt-BR, Conventional Commits, **sem** `Co-Authored-By` nem rodapés de IA.

**Commit recomendado após cada checkpoint (T003, T008, T016, T021, T027, T031)**:

| Checkpoint | Mensagem sugerida |
|---|---|
| T003 | `chore: cria app accounts` |
| T008 | `feat: adiciona modelo de usuário próprio identificado por e-mail` |
| T016 | `feat: adiciona cadastro de usuário via POST /api/usuarios/ fechável por configuração (US1)` |
| T021 | `feat: recusa e-mail já cadastrado inclusive sob concorrência (US2)` |
| T027 | `feat: valida dados do cadastro com mensagens pt-BR e senhas comuns em português (US3)` |
| T031 | `docs: documenta cadastro no README e conclui US-01` |
