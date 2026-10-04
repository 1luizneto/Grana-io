---

description: "Lista de tarefas da feature 003-login-logout (US-02 + autenticação do RNF-02)"
---

# Tasks: Login e Logout

**Input**: documentos de design em `/specs/003-login-logout/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/api-sessao.md](contracts/api-sessao.md),
[quickstart.md](quickstart.md)

**Tests**: **obrigatórios** pelo Princípio IV. Autenticação é core. Escreva os testes primeiro e
confirme que falham. Settings, compose, `.env.example` e `vite.config.js` são glue, validados pelo
[quickstart.md](quickstart.md).

**Organization**: cada fase termina num **Checkpoint**. No checkpoint, pare com a suíte verde,
apresente o resumo e sugira o commit. O commit é manual, sem trailers de IA.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**:
  - US1: entrar
  - US2: credenciais inválidas e limite de tentativas
  - US3: proteção das rotas
  - US4: renovar
  - US5: sair
- Suíte: `docker compose run --rm backend pytest`. Nos exemplos com `curl` no Git Bash, use
  `MSYS_NO_PATHCONV=1`

---

## Phase 1: Setup

**Purpose**: dependência nova e apps do simplejwt

- [X] T001 Adicionar `djangorestframework-simplejwt==5.5.1` a `backend/requirements.txt` ([research R-01, R-12](research.md))
- [X] T002 Em `backend/config/settings.py`, adicionar `"rest_framework_simplejwt"` e `"rest_framework_simplejwt.token_blacklist"` a `INSTALLED_APPS`, depois de `"rest_framework"`. Rodar `docker compose up -d --build --wait` e conferir:
  - nos logs do backend, a aplicação das migrations `token_blacklist.*`;
  - que existem as tabelas `token_blacklist_outstandingtoken` e `token_blacklist_blacklistedtoken`;
  - a suíte verde (80) e `makemigrations --check` sem pendências.

  (depende de T001)

**Checkpoint**: dependência instalada, tabelas criadas e suíte verde.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: configuração da sessão, autenticação padrão e base de testes.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T003 Escrever **primeiro** os testes de `env_int(nome, padrao)` em `backend/tests/config/test_env.py`:
  - devolve o inteiro definido (`"45"` → `45`);
  - devolve o padrão se a variável estiver ausente ou vazia;
  - lança `ImproperlyConfigured` citando o nome da variável para `"abc"`, `"0"` e `"-5"` (o valor tem de ser inteiro ≥ 1).

  Confirmar a **falha** ([research R-10](research.md)).
- [X] T004 Implementar `env_int(nome, padrao)` em `backend/config/env.py` e confirmar T003 **verde**
- [X] T005 Em `backend/config/settings.py`:
  - `SIMPLE_JWT`:
    - `ACCESS_TOKEN_LIFETIME = timedelta(minutes=env_int("GRANA_SESSAO_ACESSO_MINUTOS", 30))`;
    - `REFRESH_TOKEN_LIFETIME = timedelta(days=env_int("GRANA_SESSAO_RENOVACAO_DIAS", 7))`;
    - `ROTATE_REFRESH_TOKENS = True`, `BLACKLIST_AFTER_ROTATION = True`;
    - `UPDATE_LAST_LOGIN = False`;
    - `AUTH_HEADER_TYPES = ("Bearer",)`.
  - Em `REST_FRAMEWORK`, trocar `DEFAULT_AUTHENTICATION_CLASSES` para `["rest_framework_simplejwt.authentication.JWTAuthentication"]` e remover o comentário "JWT entra na US-02".

  ([research R-04, R-06](research.md))
- [X] T006 [P] Em `backend/tests/conftest.py`, criar um fixture `autouse` que roda `django.core.cache.cache.clear()` antes de cada teste, para isolar o limite de tentativas entre testes ([research R-11](research.md)). Criar `backend/tests/accounts/conftest.py` com:
  - `usuario`, uma conta ativa `ana@exemplo.com` / `"uma-senha-boa-2026"`, nome `"Ana Souza"`;
  - `outro_usuario`, a conta `bia@exemplo.com`;
  - `cliente`, um `APIClient` sem autenticação;
  - `cliente_autenticado`, um fixture que **recebe o fixture `usuario`** e devolve um `APIClient` já com `force_authenticate(user=usuario)`. Os testes que precisam de credencial real (JWT no cabeçalho) não usam esse fixture: fazem login ou geram o token com `AccessToken.for_user`.
- [X] T007 Adicionar ao `environment` do `backend` em `compose.yaml` as variáveis `GRANA_SESSAO_ACESSO_MINUTOS: ${GRANA_SESSAO_ACESSO_MINUTOS:-30}` e `GRANA_SESSAO_RENOVACAO_DIAS: ${GRANA_SESSAO_RENOVACAO_DIAS:-7}`. Acrescentar as duas ao `.env.example`, comentadas: "Duração da credencial de acesso, em minutos (inteiro ≥ 1)" e "Por quanto tempo a pessoa fica conectada sem digitar a senha, em dias (inteiro ≥ 1)"
- [X] T008 Rodar a suíte e confirmar que **todos os testes anteriores continuam verdes**, em especial saúde e cadastro, que são públicos e já declaram `authentication_classes = []`. Rodar `docker compose up -d --wait` e conferir `GET /api/health/` 200 e `POST /api/usuarios/` sem credencial respondendo 201 ou 400

**Checkpoint**: autenticação JWT como padrão, prazos configuráveis e rotas públicas intactas.

---

## Phase 3: User Story 1 - Entrar com e-mail e senha (Priority: P1) 🎯 MVP

**Goal**: `POST /api/auth/entrar/` devolve `acesso`, `renovacao` e `usuario`, e `GET /api/usuarios/eu/` funciona com a credencial.

**Independent Test**: quickstart S1 e S2 (primeira linha).

### Tests for User Story 1 ⚠️

- [X] T009 [P] [US1] Escrever `backend/tests/accounts/test_sessao_service.py`:
  - `autenticar(email=" ANA@Exemplo.com ", senha=...)` devolve o `usuario`;
  - `emitir_sessao(usuario)` devolve um dicionário com `acesso` e `renovacao` (strings não vazias);
  - `AccessToken(acesso)["user_id"]` corresponde ao id do usuário;
  - o `last_login` do usuário fica preenchido;
  - existe um `OutstandingToken` para a renovação emitida.
- [X] T010 [P] [US1] Escrever `backend/tests/accounts/test_entrar_api.py`:
  - `POST /api/auth/entrar/` com `{"email": " ANA@Exemplo.com ", "senha": "uma-senha-boa-2026"}` retorna 200 com as chaves **exatamente** `{"acesso", "renovacao", "usuario"}`, e `usuario == {"nome": "Ana Souza", "email": "ana@exemplo.com"}`;
  - a senha não aparece no corpo;
  - `GET /api/usuarios/eu/` com `HTTP_AUTHORIZATION=f"Bearer {acesso}"` retorna 200 com `{"nome": "Ana Souza", "email": "ana@exemplo.com"}`;
  - `SafeExceptionReporterFilter().get_post_parameters(request)` mascara `senha` na view de entrar, com `RequestFactory` e dados de formulário, como na spec 002.

  Rodar e confirmar a **falha**.

### Implementation for User Story 1

- [X] T011 [US1] Implementar em `backend/accounts/services/sessao.py`:
  - `autenticar(email, senha, request=None) -> Usuario | None`, que chama `django.contrib.auth.authenticate(request, email=email, password=senha)`;
  - `emitir_sessao(usuario) -> dict`, que usa `RefreshToken.for_user(usuario)`, chama `update_last_login(None, usuario)` e devolve `{"acesso": str(refresh.access_token), "renovacao": str(refresh)}`.

  ([research R-03, R-04](research.md))
- [X] T012 [US1] Adicionar a `backend/accounts/serializers.py`:
  - `EntrarSerializer`, com `email = CharField()` e `senha = CharField(trim_whitespace=False)`, os dois obrigatórios;
  - `UsuarioSerializer(ModelSerializer)`, com `fields = ["nome", "email"]`.

  Opcional: trocar o `UsuarioCadastradoSerializer` da spec 002 pelo `UsuarioSerializer`, mantendo o mesmo contrato.
- [X] T013 [US1] Implementar em `backend/accounts/views.py`:
  - `EntrarView(APIView)`:
    - `AllowAny`, `authentication_classes = []`, só `post`/`options`;
    - `sensitive_post_parameters("senha")`;
    - valida com `EntrarSerializer`, chama `autenticar` e, se houver usuário, responde 200 com `{**emitir_sessao(usuario), "usuario": UsuarioSerializer(usuario).data}`;
    - o caminho de recusa é implementado na US2 (T018); até lá, pode responder 401 com a mensagem genérica.
  - `EuView(APIView)`: `IsAuthenticated` padrão, só `get`/`head`/`options`, devolve `UsuarioSerializer(request.user).data`.
- [X] T014 [US1] Registrar em `backend/accounts/urls.py` as rotas `path("auth/entrar/", EntrarView.as_view(), name="entrar")` e `path("usuarios/eu/", EuView.as_view(), name="eu")`. `usuarios/eu/` deve vir **antes** de `usuarios/`. Rodar a suíte e confirmar T009 e T010 **verdes**
- [X] T015 [US1] Validar o S1 e o S2 (primeira linha) do [quickstart.md](quickstart.md) no ambiente real, com uma conta criada pelo cadastro

  > **Resultado (2026-10-04)**: ✅ 93 testes verdes.
  > - S1: login com `" ANA@Exemplo.com "` devolve `acesso`, `renovacao` e `usuario`, e o
  >   `last_login` fica preenchido.
  > - S2: `/usuarios/eu/` responde 200 com a credencial, direto (8000) e pelo proxy (5173).
  > - Na T013, a `EntrarView` já responde 401 com a mensagem genérica quando `autenticar` devolve
  >   `None`. A T018 cobre esse caminho com testes.
  > - O `UsuarioCadastradoSerializer` foi renomeado para `UsuarioSerializer` (opção da T012),
  >   mantendo o contrato do cadastro.

**Checkpoint**: login e consulta da própria conta funcionando; suíte verde.

---

## Phase 4: User Story 2 - Recusar credenciais inválidas e limitar tentativas (Priority: P1)

**Goal**: e-mail inexistente, senha errada e conta desativada recebem resposta idêntica, "E-mail ou senha incorretos." (401); campos ausentes, 400; mais de 10 tentativas por minuto por dispositivo, 429.

**Independent Test**: quickstart S3 e S7.

### Tests for User Story 2 ⚠️

- [X] T016 [P] [US2] Adicionar a `backend/tests/accounts/test_entrar_api.py`:
  - para `ninguem@exemplo.com`, para `ana@exemplo.com` com senha errada e para `ana@exemplo.com` desativada (`is_active=False`) com a senha certa, as respostas têm **o mesmo** `status_code` (401) e **o mesmo** corpo, `{"detail": "E-mail ou senha incorretos."}`, e nenhum `OutstandingToken` é criado;
  - `{}` retorna 400 com `{"email": ["Este campo é obrigatório."], "senha": ["Este campo é obrigatório."]}`.

  > **Nota (2026-10-04)**: estes testes **passaram de primeira**, sem fase vermelha, porque o
  > caminho de recusa já tinha entrado na T013 (permitido pela própria T013). Eles ficam como
  > cobertura do FR-003 e do FR-004.
- [X] T017 [P] [US2] Escrever `backend/tests/accounts/test_throttles.py` (com `override_settings` para a taxa `"login": "3/min"`):
  - pelo cliente de teste, 3 tentativas de login passam (401 ou 200) e a 4ª retorna 429 com `{"detail": "Muitas tentativas. Tente novamente em instantes."}` e o cabeçalho `Retry-After`;
  - **também com a senha certa** na 4ª;
  - `TentativasLoginThrottle().get_ident(request)`:
    - com `REMOTE_ADDR` igual ao IP do proxy confiável (via `monkeypatch` de `socket.gethostbyname` ou do método que resolve o proxy) e `HTTP_X_FORWARDED_FOR="10.0.0.7, 192.168.1.50"`, devolve `"192.168.1.50"`;
    - com `REMOTE_ADDR` de outro endereço e o mesmo cabeçalho, devolve o próprio `REMOTE_ADDR`, ou seja, um `X-Forwarded-For` falso não troca o dispositivo;
  - dois dispositivos diferentes atrás do proxy têm contagens independentes.

  Rodar e confirmar a **falha**.

### Implementation for User Story 2

- [X] T018 [US2] Na `EntrarView`, em `backend/accounts/views.py`, responder **401** `{"detail": "E-mail ou senha incorretos."}` sempre que `autenticar` devolver `None`. O `ModelBackend` já devolve `None` para e-mail inexistente, senha errada e conta inativa ([research R-03](research.md))
- [X] T019 [US2] Implementar `backend/accounts/throttles.py`:
  - `TentativasLoginThrottle(SimpleRateThrottle)`, com `scope = "login"` e `get_cache_key` usando `self.get_ident(request)`;
  - `get_ident` resolve `settings.PROXY_CONFIAVEL` com `socket.gethostbyname`, com cache de 60 s e tolerância a falha de resolução (nesse caso, usa `REMOTE_ADDR`). Se `REMOTE_ADDR` for esse IP e houver `X-Forwarded-For`, usa o **último** endereço do cabeçalho; senão, usa `REMOTE_ADDR`;
  - uma exceção `MuitasTentativas(Throttled)` com a mensagem fixa da spec, sem o sufixo de segundos, preservando o `wait` para o `Retry-After`.

  ([research R-07, R-08](research.md))
- [X] T020 [US2] Em `backend/config/settings.py`:
  - `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"login": f"{env_int('GRANA_LOGIN_TENTATIVAS_POR_MINUTO', 10)}/min"}`;
  - `PROXY_CONFIAVEL = env_str("GRANA_PROXY_CONFIAVEL", "frontend")`.

  Na `EntrarView`, definir `throttle_classes = [TentativasLoginThrottle]` e sobrescrever `throttled(request, wait)` para lançar `MuitasTentativas(wait=wait)`. Rodar e confirmar T016 e T017 **verdes**.

  > **Desvio na implementação**: a taxa **não** fica em `DEFAULT_THROTTLE_RATES`. O DRF lê esse
  > dicionário uma vez, ao carregar a classe, e o `override_settings` dos testes não teria efeito.
  > A solução foi o setting `LOGIN_TENTATIVAS_POR_MINUTO`, lido por `TentativasLoginThrottle.get_rate()`
  > a cada requisição.
- [X] T021 [US2] Em `frontend/vite.config.js`, adicionar `xfwd: true` ao proxy `/api`, com um comentário citando o limite de tentativas. Se o Vite 8 não aplicar o `xfwd`, trocar por `configure: (proxy) => proxy.on("proxyReq", (req, pedido) => req.setHeader("X-Forwarded-For", pedido.socket.remoteAddress))`. Rodar `docker compose up -d --build --wait`, porque o `vite.config.js` fica na imagem (spec 001 R-09)
- [X] T022 [US2] Adicionar ao `compose.yaml` (backend) as variáveis `GRANA_LOGIN_TENTATIVAS_POR_MINUTO: ${GRANA_LOGIN_TENTATIVAS_POR_MINUTO:-10}` e `GRANA_PROXY_CONFIAVEL: ${GRANA_PROXY_CONFIAVEL:-frontend}`, e comentá-las no `.env.example`. Validar o S3 e o S7 do [quickstart.md](quickstart.md): pela porta 5173, a 11ª tentativa dá 429. **No Docker Desktop, a porta 8000 e outros dispositivos compartilham a mesma contagem**, como documentado na spec (Edge Cases) e no research R-08; registrar o comportamento observado. Comentar no `.env.example`, junto de `GRANA_LOGIN_TENTATIVAS_POR_MINUTO`, que no Docker Desktop o limite vale para todos os dispositivos juntos

  > **Resultado (2026-10-04)**: ✅ 101 testes verdes.
  > - S3: e-mail inexistente recebe 401 "E-mail ou senha incorretos.", e `{}` recebe 400 com os
  >   dois campos obrigatórios.
  > - S7: 10 × 401 e a 11ª com 429, a mensagem da spec e `Retry-After: 58`. Logo em seguida, a
  >   porta 8000 também deu 429, como esperado no Docker Desktop.
  > **Achado e correção**: na primeira rodada, a porta 8000 deu **401**, ou seja, uma contagem
  > separada. O Vite (Node) escuta em IPv6 e encaminha clientes IPv4 como `::ffff:a.b.c.d`
  > (confirmado num container: `::ffff:127.0.0.1`), enquanto o Django recebe `a.b.c.d`, e o mesmo
  > dispositivo contava em dobro. O `get_ident` passou a normalizar o prefixo, com um teste novo
  > em `test_throttles.py`.

**Checkpoint**: login seguro contra enumeração e adivinhação; suíte verde.

---

## Phase 5: User Story 3 - Proteger o que exige sessão (Priority: P1)

**Goal**: tudo exige credencial de acesso, exceto saúde, cadastro, entrar e renovar; 401 distingue ausência de credencial de credencial inválida ou vencida.

**Independent Test**: quickstart S2 (linhas 2 e 3), S6 e S8.

### Tests for User Story 3 ⚠️

- [X] T023 [P] [US3] Escrever `backend/tests/accounts/test_protecao_api.py`:
  - `GET /api/usuarios/eu/`:
    - sem credencial → 401, `detail == "As credenciais de autenticação não foram fornecidas."` e cabeçalho `WWW-Authenticate` começando com `Bearer`;
    - com `Bearer abc.def.ghi` → 401 e `code == "token_not_valid"`;
    - com credencial **vencida** (gerar `AccessToken.for_user(usuario)` e chamar `set_exp(lifetime=-timedelta(seconds=1))`) → 401 e `code == "token_not_valid"`;
    - com credencial válida de conta desativada depois da emissão → 401 e `code == "user_inactive"`;
  - com duas contas, `/usuarios/eu/` devolve só os dados da conta dona da credencial (isolamento, Princípio II);
  - as rotas públicas `GET /api/health/`, `POST /api/usuarios/` e `POST /api/auth/entrar/` **não** respondem 401 sem credencial;
  - guarda de regressão: percorrer `get_resolver().url_patterns` (recursivo) e, para cada rota de API que não seja uma das 4 públicas, garantir que a view tem `IsAuthenticated` nas permissões efetivas. Uma rota nova sem proteção quebra o teste.

  Rodar e confirmar o que falha. O caso da guarda precisa conhecer a rota `auth/renovar/`, que ainda não existe; deixar a lista de públicas completa desde já.

### Implementation for User Story 3

- [X] T024 [US3] Confirmar a T023 **verde** **sem mudar código de produção**: a autenticação padrão (T005) e a `EuView` (T013) já devem atender. A rota `auth/renovar/` ainda não existe e só está na lista de públicas da guarda, sem efeito até a US4. Se algum teste exigir mudança de código, ela precisa ser registrada nesta tarefa, com o motivo, antes do checkpoint
- [X] T025 [US3] Validar S2 (linhas 2 e 3), S6 e S8 do [quickstart.md](quickstart.md)

  > **Resultado (2026-10-04)**: ✅ 110 testes verdes.
  > - Os 9 testes da T023 **passaram de primeira**, como previsto: a US3 só comprova o que a
  >   autenticação padrão (T005) e a `EuView` (T013) já fazem. Nenhum código de produção mudou
  >   (T024).
  > - Para garantir que a guarda funciona de verdade, listei a classificação: as 3 públicas
  >   aparecem como desprotegidas e passam só por estarem na lista, e `usuarios/eu/` aparece como
  >   protegida.
  > - No ambiente real:
  >   - S2: sem credencial, 401 "As credenciais de autenticação não foram fornecidas."; adulterada,
  >     401 `token_not_valid`;
  >   - S6: conta desativada, 401 `user_inactive` em `/eu/` e login com a mensagem genérica;
  >     reativada, 200. A parte de renovar fica para a T030;
  >   - S8: health 200 e cadastro 400 sem credencial.

**Checkpoint**: proteção comprovada e guarda contra rotas novas desprotegidas; suíte verde.

---

## Phase 6: User Story 4 - Sessão que expira e pode ser renovada (Priority: P2)

**Goal**: `POST /api/auth/renovar/` troca a credencial de renovação por um par novo; a antiga deixa de valer.

**Independent Test**: quickstart S4.

### Tests for User Story 4 ⚠️

- [ ] T026 [P] [US4] Adicionar a `backend/tests/accounts/test_sessao_service.py`:
  - `renovar_sessao(renovacao)` devolve um novo par `acesso`/`renovacao`, com a renovação diferente da anterior;
  - a renovação anterior fica em `BlacklistedToken`;
  - usar de novo a antiga lança `SessaoInvalida`;
  - renovação vencida (via `set_exp` com lifetime negativo), adulterada ou de conta desativada lança `SessaoInvalida`.
- [ ] T027 [P] [US4] Escrever `backend/tests/accounts/test_renovar_sair_api.py`, parte "renovar":
  - `POST /api/auth/renovar/` com renovação válida → 200 com as chaves **exatamente** `{"acesso", "renovacao"}`, e o novo `acesso` funciona em `/usuarios/eu/`;
  - com a mesma renovação de novo → 401 `{"detail": "Sessão expirada ou encerrada. Entre novamente."}`;
  - `{}` → 400 com `renovacao: ["Este campo é obrigatório."]`;
  - adulterada → 401 com a mesma mensagem;
  - `SafeExceptionReporterFilter().get_post_parameters(request)` mascara `renovacao` na view de renovar, com `RequestFactory` e dados de formulário (FR-013).

  Rodar e confirmar a **falha**.

### Implementation for User Story 4

- [ ] T028 [US4] Implementar em `backend/accounts/services/sessao.py`:
  - `class SessaoInvalida(Exception)`;
  - `renovar_sessao(renovacao) -> dict`, que usa `rest_framework_simplejwt.serializers.TokenRefreshSerializer(data={"refresh": renovacao})`. Com `is_valid(raise_exception=True)` dentro de `try`, captura `TokenError`, `InvalidToken`, `AuthenticationFailed` e `ValidationError` e relança como `SessaoInvalida`. Devolve `{"acesso": data["access"], "renovacao": data["refresh"]}`.

  ([research R-04](research.md))
- [ ] T029 [US4] Adicionar `RenovacaoSerializer` (`renovacao = CharField()`) a `backend/accounts/serializers.py`. Em `backend/accounts/views.py`, criar a `RenovarView`:
  - `AllowAny`, `authentication_classes = []`, só `post`;
  - `sensitive_post_parameters("renovacao")`;
  - converte `SessaoInvalida` em 401 com a mensagem do contrato.

  Registrar `path("auth/renovar/", ...)` em `backend/accounts/urls.py`. Rodar e confirmar T026, T027 e a guarda da T023 **verdes**.
- [ ] T030 [US4] Validar o S4 do [quickstart.md](quickstart.md)

**Checkpoint**: renovação de uso único; suíte verde.

---

## Phase 7: User Story 5 - Sair do sistema (Priority: P2)

**Goal**: `POST /api/auth/sair/` (protegida) bloqueia a credencial de renovação do próprio usuário; as outras sessões continuam.

**Independent Test**: quickstart S5.

### Tests for User Story 5 ⚠️

- [ ] T031 [P] [US5] Adicionar a `backend/tests/accounts/test_sessao_service.py`:
  - `encerrar_sessao(usuario, renovacao)` bloqueia a renovação, que deixa de renovar;
  - com a renovação de **outro** usuário, lança `SessaoInvalida` e **não** bloqueia nada;
  - com renovação já bloqueada, vencida ou adulterada, lança `SessaoInvalida`.
- [ ] T032 [P] [US5] Adicionar a `backend/tests/accounts/test_renovar_sair_api.py`, parte "sair":
  - com o par A, `POST /api/auth/sair/` usando `Authorization: Bearer <acesso A>` e `{"renovacao": <A>}` retorna 204; renovar A dá 401, e renovar B, da mesma conta, dá 200;
  - sem credencial de acesso → 401;
  - com o acesso da Bia e a renovação da Ana → 400 `{"renovacao": ["Sessão inválida ou já encerrada."]}`, e a renovação da Ana continua funcionando;
  - `{}` → 400 com "Este campo é obrigatório.";
  - `SafeExceptionReporterFilter().get_post_parameters(request)` mascara `renovacao` na view de sair, com `RequestFactory`, dados de formulário e `force_authenticate` (FR-013).

  Rodar e confirmar a **falha**.

### Implementation for User Story 5

- [ ] T033 [US5] Implementar `encerrar_sessao(usuario, renovacao)` em `backend/accounts/services/sessao.py`:
  1. `token = RefreshToken(renovacao)`, que já recusa vencida, adulterada e bloqueada; se lançar `TokenError`, relançar como `SessaoInvalida`;
  2. se `str(token[api_settings.USER_ID_CLAIM]) != str(usuario.pk)`, lançar `SessaoInvalida`, com `from rest_framework_simplejwt.settings import api_settings`;
  3. `token.blacklist()`.

  ([research R-05](research.md))
- [ ] T034 [US5] Criar em `backend/accounts/views.py` a `SairView`:
  - protegida (padrão), só `post`;
  - `sensitive_post_parameters("renovacao")`;
  - valida com `RenovacaoSerializer`, chama `encerrar_sessao(request.user, ...)` e responde 204;
  - `SessaoInvalida` vira 400 com a mensagem do contrato.

  Registrar `path("auth/sair/", ...)`. Confirmar T031 e T032 **verdes**.
- [ ] T035 [US5] Validar o S5 do [quickstart.md](quickstart.md)

**Checkpoint**: saída funcionando, sem afetar outras sessões nem aceitar credencial de outra pessoa; suíte verde.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T036 [P] Atualizar o `README.md`:
  - na seção 3, acrescentar as rotas de sessão e a própria conta, com exemplo de login e de uso do `Authorization: Bearer`, e link para [contracts/api-sessao.md](contracts/api-sessao.md);
  - na seção 7, explicar as 4 variáveis novas;
  - acrescentar uma nota sobre a limpeza periódica com `docker compose exec backend python manage.py flushexpiredtokens`;
  - atualizar o "Estado atual".
- [ ] T037 [P] Acrescentar as 4 variáveis novas à tabela "Configuráveis" de `specs/001-infra-docker/contracts/environment.md`, com referência a esta spec
- [ ] T038 Executar o [quickstart.md](quickstart.md) completo (S1 a S10) e registrar o resultado. Conferir também `makemigrations --check` e o S9 (nenhum `eyJ`, nenhuma senha nos logs)
- [ ] T039 Fechar a Definition of Done:
  - suíte verde e todas as tarefas marcadas;
  - em `BACKLOG.md`, marcar ☑ na US-02 os critérios "Login com e-mail e senha retorna um token/sessão válido", "Credenciais inválidas exibem mensagem genérica" e "O token expira após um período definido e pode ser renovado". Os dois critérios de redirecionamento continuam ☐, anotados como cobertos pela US-26;
  - no RNF-02, marcar ☑ "A API exige autenticação em todas as rotas, exceto login e cadastro".

**Checkpoint**: feature pronta para PR na `main`.

---

## Dependencies & Execution Order

```text
Setup → Foundational → US1 → US2 ─┐
                          └→ US3 ─┼→ US4 → US5 → Polish
```

- **US1** é a base de todas as outras, porque é quem gera as credenciais.
- **US2** e **US3** dependem só da US1 e podem vir em qualquer ordem. A guarda da T023 fica
  completa depois da US4, que cria a rota `auth/renovar/`.
- **US5** depende da US4, porque os testes usam a renovação para provar a saída.
- `backend/accounts/views.py`, `serializers.py`, `services/sessao.py`, `urls.py`,
  `config/settings.py`, `compose.yaml` e `.env.example` são editados por várias fases, sempre em
  sequência.

### Parallel Opportunities

- US1: T009 ∥ T010.
- US2: T016 ∥ T017.
- US4: T026 ∥ T027.
- US5: T031 ∥ T032.
- Foundational: T006 ∥ T003.
- Polish: T036 ∥ T037.

## Parallel Example: User Story 1

```bash
Task: "T009 Testes do service de sessão em backend/tests/accounts/test_sessao_service.py"
Task: "T010 Testes da API de entrar em backend/tests/accounts/test_entrar_api.py"
```

## Implementation Strategy

### MVP First

Setup + Foundational + US1 + US2 + US3: login seguro, com rotas protegidas. Com isso a US-03
(isolamento) já pode começar. A renovação e a saída (US4, US5) completam a US-02.

### Incremental Delivery

Um checkpoint por fase, cada um com a suíte verde e validado pelo quickstart.

## Notes

- **T002 e T021 exigem rebuild** (`--build`): o `requirements.txt` e o `vite.config.js` ficam dentro
  das imagens.
- **O throttle usa o cache em memória**: o fixture de limpeza (T006) é obrigatório, senão os
  testes interferem entre si.
- Commits manuais, pt-BR, Conventional Commits, **sem** `Co-Authored-By` nem rodapés de IA.

**Commit recomendado após cada checkpoint (T002, T008, T015, T022, T025, T030, T035, T039)**:

| Checkpoint | Mensagem sugerida |
|---|---|
| T002 | `chore: adiciona djangorestframework-simplejwt com lista de bloqueio` |
| T008 | `feat: configura autenticação JWT padrão com prazos de sessão configuráveis` |
| T015 | `feat: adiciona login por e-mail e consulta da própria conta (US1)` |
| T022 | `feat: recusa credenciais com mensagem genérica e limita tentativas de login (US2)` |
| T025 | `test: garante proteção das rotas e distingue erros de autenticação (US3)` |
| T030 | `feat: adiciona renovação de sessão de uso único (US4)` |
| T035 | `feat: adiciona saída que encerra só a sessão do próprio usuário (US5)` |
| T039 | `docs: documenta sessão no README e conclui US-02` |
