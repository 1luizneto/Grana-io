---

description: "Lista de tarefas da feature 001-infra-docker (RNF-01 + infraestrutura do RNF-02)"
---

# Tasks: Execução Local com Um Comando (Infraestrutura Docker)

**Input**: documentos de design em `/specs/001-infra-docker/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: **obrigatórios** para o core, pelo Princípio IV da constituição (endpoint de saúde,
service de verificação do banco, helpers de ambiente, bloqueio da chave secreta, CORS,
migrations pendentes). Escreva os testes primeiro e confirme que falham antes de implementar. O
glue (Dockerfiles, compose, settings, scripts, frontend provisório) é validado pelos cenários do
[quickstart.md](quickstart.md).

**Organization**: as tarefas estão agrupadas por user story, e cada fase termina num
**Checkpoint** (marco de commit). No checkpoint, pare com os testes verdes, apresente o resumo das
mudanças e sugira a mensagem de commit. O commit é feito manualmente pelo responsável, sem
trailers de IA.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: user story da tarefa (US1 a US5)
- Todos os caminhos são relativos à raiz do repositório

## Path Conventions

- Aplicação web: `backend/` (Django) e `frontend/` (React + Vite), com `compose.yaml` na raiz
- Testes do backend em `backend/tests/<app>/`, espelhando os apps (`docs/arquitetura.md` §2.3)
- Comando da suíte: `docker compose run --rm backend pytest`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: esqueleto de arquivos do repositório, do backend e do frontend

- [X] T001 [P] Criar `.gitattributes` na raiz com `* text=auto eol=lf` e marcar como `binary` os padrões `*.png *.jpg *.jpeg *.gif *.ico *.webp *.woff *.woff2 *.pdf` (FR-016, research R-10)
- [X] T002 [P] Criar `.gitignore` na raiz ignorando `.env`, `.env.*` (com exceção `!.env.example`), `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.venv/`, `node_modules/`, `frontend/dist/`, `*.log` e `.DS_Store` (FR-011)
- [X] T003 [P] Criar `backend/requirements.txt` com versões **exatas** (`==`, última patch estável no PyPI no momento da implementação) de `Django` (série 5.2 LTS), `djangorestframework`, `psycopg[binary]` (3.x) e `django-cors-headers`. Criar `backend/requirements-dev.txt` com `-r requirements.txt` + `pytest` e `pytest-django`, também com versões exatas (research R-15)
- [X] T004 [P] Criar `backend/Dockerfile`: base `python:3.12-slim`, `ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1`, `WORKDIR /app`, copiar `requirements*.txt`, `pip install --no-cache-dir -r requirements-dev.txt`, `COPY . .`, `EXPOSE 8000` e `CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]`. Criar `backend/.dockerignore` com `__pycache__/`, `*.pyc`, `.pytest_cache/` e `.env` (research R-01, R-17)
- [X] T005 [P] Criar os arquivos padrão do projeto Django com `DJANGO_SETTINGS_MODULE=config.settings`: `backend/manage.py`, `backend/config/__init__.py`, `backend/config/wsgi.py` e `backend/config/asgi.py` (conteúdo equivalente ao de `django-admin startproject config`)
- [X] T006 [P] Criar o app `core`: `backend/core/__init__.py`, `backend/core/apps.py` (`CoreConfig`, `name = "core"`, `default_auto_field = "django.db.models.BigAutoField"`), `backend/core/services/__init__.py` e `backend/core/urls.py` com `urlpatterns = []`
- [X] T007 [P] Criar o esqueleto do frontend. `frontend/package.json` com `"name": "grana-frontend"`, `"private": true`, `"type": "module"`, os scripts `dev` (`vite`), `build` (`vite build`) e `preview` (`vite preview`), as dependências `react` e `react-dom` (19.x) e as devDependencies `vite` e `@vitejs/plugin-react`. `frontend/index.html` com `lang="pt-BR"`, `<title>Grana.io</title>`, `<div id="root">` e `<script type="module" src="/src/main.jsx">`. `frontend/src/main.jsx` com `createRoot` + `StrictMode` renderizando `App`. `frontend/src/App.jsx` provisório exibindo `Grana.io`. Nenhum recurso externo (fontes, CDN), pelo Princípio I
- [X] T008 [P] Criar `frontend/Dockerfile`: base `node:24-alpine`, `WORKDIR /app`, copiar `package.json` e `package-lock.json`, `RUN npm ci`, `COPY . .`, `EXPOSE 5173` e `CMD ["npm", "run", "dev"]`. Criar `frontend/.dockerignore` com `node_modules/`, `dist/` e `.env` (research R-01)
- [X] T009 [P] Criar `frontend/vite.config.js` com o plugin React e `server: { host: true, port: 5173, strictPort: true, watch: { usePolling: true, interval: 300 }, proxy: { '/api': { target: process.env.API_PROXY_TARGET ?? 'http://backend:8000', changeOrigin: true } } }` (research R-06, R-07, R-09)
- [X] T010 Gerar `frontend/package-lock.json` sem Node na máquina, rodando no PowerShell a partir da raiz: `docker run --rm -v "${PWD}/frontend:/app" -w /app node:24-alpine npm install`. Conferir que o lockfile foi criado e que `frontend/node_modules/` está ignorado pelo Git (depende de T007)

**Checkpoint**: esqueleto criado; `git status` mostra só arquivos esperados (sem `node_modules` nem `.env`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: banco + backend no Compose, settings 12-factor e suíte de testes rodando com um comando. Isso é pré-requisito do test-first de todas as histórias.

**⚠️ CRITICAL**: nenhuma user story começa antes desta fase terminar.

- [ ] T011 Criar `compose.yaml` na raiz. Usar `name: grana` e uma âncora `x-postgres-env: &postgres-env` com `POSTGRES_DB: ${POSTGRES_DB:-grana}`, `POSTGRES_USER: ${POSTGRES_USER:-grana}` e `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-grana-dev-senha}`. O serviço `db` usa `image: postgres:17-alpine`, `environment: *postgres-env`, healthcheck `["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]` (interval 5s, timeout 5s, retries 10) e **sem `ports:`** (FR-019). O serviço `backend` usa `build: ./backend`; `environment` com `<<: *postgres-env`, `POSTGRES_HOST: db`, `POSTGRES_PORT: "5432"`, `DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:-}`, `DJANGO_DEBUG: ${DJANGO_DEBUG:-1}` e `DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS:-*}`; `ports: ["${BACKEND_PORT:-8000}:8000"]`; `volumes: ["./backend:/app"]`; `depends_on: { db: { condition: service_healthy } }` (FR-003, FR-009, FR-010, research R-02, R-03, R-04, R-08)
- [ ] T012 Criar `backend/pytest.ini` com `DJANGO_SETTINGS_MODULE = config.settings`, `testpaths = tests`, `python_files = test_*.py` e `addopts = -ra`. Criar os pacotes de teste `backend/tests/__init__.py`, `backend/tests/conftest.py` (vazio por enquanto), `backend/tests/config/__init__.py` e `backend/tests/core/__init__.py`
- [ ] T013 Escrever **primeiro** os testes dos helpers de ambiente em `backend/tests/config/test_env.py`, usando `monkeypatch`. Casos:
  - `env_str(nome, padrao="")` retorna o valor definido, ou o padrão se a variável estiver ausente;
  - `env_bool(nome, padrao=False)` retorna verdadeiro para `1/true/yes/on` (sem diferenciar maiúsculas), falso para qualquer outro valor, e o padrão se ausente;
  - `env_list(nome)` separa por vírgula, remove espaços e ignora itens vazios (`"a, ,b,"` → `["a", "b"]`), e retorna `[]` se ausente ou vazio.

  Rodar `docker compose run --rm backend pytest` e confirmar a **falha**: `config.env` e `config.settings` ainda não existem (data-model §2)
- [ ] T014 Implementar `backend/config/env.py` com `env_str`, `env_bool`, `env_list` e a constante `CHAVE_DEV_PADRAO = "django-insecure-grana-dev-troque-me"` (research R-03, R-12)
- [ ] T015 Implementar `backend/config/settings.py` 12-factor usando `config.env`:
  - `SECRET_KEY = env_str("DJANGO_SECRET_KEY") or CHAVE_DEV_PADRAO`
  - `DEBUG = env_bool("DJANGO_DEBUG", False)`
  - `ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")`
  - `INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "django.contrib.staticfiles", "rest_framework", "core"]`
  - `MIDDLEWARE = [SecurityMiddleware, CommonMiddleware, XFrameOptionsMiddleware]`
  - `TEMPLATES` padrão (`DjangoTemplates`, `APP_DIRS=True`)
  - `DATABASES["default"]` PostgreSQL a partir de `POSTGRES_DB/USER/PASSWORD/HOST/PORT` (padrões `grana`, `grana`, `""`, `db`, `5432`)
  - `LANGUAGE_CODE = "pt-br"`, `TIME_ZONE = "America/Sao_Paulo"`, `USE_I18N = True`, `USE_TZ = True`
  - `STATIC_URL = "static/"`, `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"`, `ROOT_URLCONF = "config.urls"`, `WSGI_APPLICATION = "config.wsgi.application"`
  - `REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": [], "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"], "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"]}`. Comentar que a autenticação JWT entra na US-02.

  (research R-11; constituição, Stack & Technology Constraints)
- [ ] T016 Implementar `backend/config/urls.py` com `urlpatterns = [path("api/", include("core.urls"))]`
- [ ] T017 Rodar `docker compose build backend` e `docker compose run --rm backend pytest` e confirmar os testes de T013 **verdes**. Rodar `docker compose up -d --wait db backend` e confirmar em `docker compose logs backend` que o servidor iniciou após o `db` ficar `healthy`. Encerrar com `docker compose down`

**Checkpoint**: `docker compose run --rm backend pytest` verde; backend sobe conectado ao banco. A partir daqui as user stories podem começar.

---

## Phase 3: User Story 1 - Subir o sistema inteiro com um comando (Priority: P1) 🎯 MVP

**Goal**: um `docker compose up` coloca banco, API e interface no ar; a API expõe `GET /api/health/` e a página inicial mostra se a API está acessível, inclusive por outro dispositivo da rede.

**Independent Test**: num clone limpo, `docker compose up -d --wait` → `http://localhost:8000/api/health/` retorna 200 `{"status": "ok", "database": "ok"}` e `http://localhost:5173` (e `http://<IP>:5173` no celular) mostra "API acessível" (quickstart V1–V4).

### Tests for User Story 1 ⚠️

> Escreva estes testes primeiro e confirme que falham antes de implementar.

- [ ] T018 [P] [US1] Escrever os testes do service em `backend/tests/core/test_saude_service.py`:
  - `verificar_banco()` retorna `True` com o banco acessível (`@pytest.mark.django_db`);
  - retorna `False` quando `connection.cursor` lança `django.db.OperationalError` (via `monkeypatch`).
- [ ] T019 [P] [US1] Escrever os testes do endpoint em `backend/tests/core/test_health.py`, conforme [contracts/api-health.md](contracts/api-health.md) e usando `rest_framework.test.APIClient` sem autenticação:
  - `GET /api/health/` retorna 200 e o corpo é **exatamente** `{"status": "ok", "database": "ok"}`;
  - com `core.views.verificar_banco` substituído para retornar `False`, retorna 503 e o corpo é **exatamente** `{"status": "error", "database": "unavailable"}` (sem chaves extras, mensagens de exceção, host ou credenciais);
  - `POST /api/health/` retorna 405.

  Rodar a suíte e confirmar a **falha**.

### Implementation for User Story 1

- [ ] T020 [US1] Implementar `backend/core/services/saude.py` com `verificar_banco() -> bool`. A função executa `SELECT 1` via `connection.cursor()`, captura **somente** `django.db.Error` e retorna `False` nesse caso, sem logar nem propagar detalhes (research R-11)
- [ ] T021 [US1] Implementar `SaudeView(APIView)` em `backend/core/views.py`, que importa `verificar_banco` de `core.services.saude`, com:
  - `permission_classes = [AllowAny]`, `authentication_classes = []`, `http_method_names = ["get", "head", "options"]`;
  - `get()` devolve 200 `{"status": "ok", "database": "ok"}` ou 503 `{"status": "error", "database": "unavailable"}`.

  A view é fina, sem regra (`docs/arquitetura.md` §2.1). Nome em pt-BR com sufixo técnico, e rota
  `/api/health/` mantida em inglês por convenção de infraestrutura (`docs/arquitetura.md` §4,
  "Nomenclatura").
- [ ] T022 [US1] Registrar `path("health/", SaudeView.as_view(), name="saude")` em `backend/core/urls.py`. Rodar `docker compose run --rm backend pytest` e confirmar T018 e T019 **verdes**
- [ ] T023 [P] [US1] Implementar o cliente de API centralizado em `frontend/src/api/client.js`:
  - `const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')`;
  - `export async function requisitar(caminho, opcoes = {})` faz `fetch(`${API_BASE}${caminho}`, { headers: { Accept: 'application/json' }, signal: AbortSignal.timeout(5000), ...opcoes })` e devolve a `Response`.

  Os componentes nunca chamam `fetch` diretamente (research R-06; `docs/arquitetura.md` §3).
- [ ] T024 [US1] Implementar `obterSaude()` em `frontend/src/api/saude.js`. A função chama `requisitar('/health/')` e retorna `'ok'` (200 com `database === 'ok'`), `'banco-indisponivel'` (503) ou `'inacessivel'` (outro status, erro de rede ou timeout), sem lançar exceção (contrato "Consumo pelo frontend") (depende de T023)
- [ ] T025 [US1] Implementar o hook `useSaudeApi()` em `frontend/src/hooks/useSaudeApi.js`. O estado inicial é `'carregando'`; o hook chama `obterSaude()` ao montar, atualiza o estado e ignora o resultado se o componente já tiver desmontado (depende de T024)
- [ ] T026 [US1] Implementar a página `frontend/src/pages/Inicio/Inicio.jsx`, com título `Grana.io` e as mensagens pt-BR por estado:
  - `carregando` → "Verificando a API…"
  - `ok` → "API acessível (banco operacional)"
  - `banco-indisponivel` → "API acessível, banco indisponível"
  - `inacessivel` → "API inacessível"

  Atualizar `frontend/src/App.jsx` para renderizar `<Inicio />` (FR-008) (depende de T025).
- [ ] T027 [US1] Atualizar `compose.yaml`:
  - no `backend`, healthcheck `["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/', timeout=3)"]` (interval 10s, timeout 5s, retries 5, start_period 30s);
  - novo serviço `frontend` com `build: ./frontend`, `environment: { API_PROXY_TARGET: http://backend:8000, VITE_API_URL: ${VITE_API_URL:-} }`, `ports: ["${FRONTEND_PORT:-5173}:5173"]`, `volumes: ["./frontend:/app", "/app/node_modules"]` e `depends_on: [backend]`.

  (FR-001, FR-015, FR-018; research R-06, R-08, R-09)
- [ ] T028 [US1] Validar pelo [quickstart.md](quickstart.md):
  - V1 (exceto o passo 4, sobre migrations, que é validado na US4), V2, V3 e V4;
  - V8 (recarga sem rebuild no backend e no frontend; FR-015), para detectar cedo qualquer
    problema de polling nos bind mounts do Windows;
  - `docker compose down` encerra todos os serviços (US1, cenário 5).

  Registrar o resultado no resumo do checkpoint.

**Checkpoint**: US1 funcional e demonstrável sozinha: sistema sobe com um comando, saúde 200/503 conforme o banco, página inicial mostra o estado da API no PC e no celular. Suíte verde.

---

## Phase 4: User Story 2 - Dados preservados entre reinicializações (Priority: P1)

**Goal**: os dados do banco sobrevivem a `down`/`up`, reboot e rebuild, e só `docker compose down -v` os apaga.

**Independent Test**: quickstart V5 (registro sobrevive a 5 ciclos e a um rebuild; some após `down -v`).

### Implementation for User Story 2

- [ ] T029 [US2] Em `compose.yaml`, declarar o volume nomeado de topo `volumes: { pgdata: {} }` e montá-lo no `db` em `pgdata:/var/lib/postgresql/data`. Confirmar que `name: grana` resolve o volume como `grana_pgdata` (`docker volume ls`) (FR-005, FR-006, data-model §1, research R-05)
- [ ] T030 [US2] Validar o cenário V5 do [quickstart.md](quickstart.md): 5 ciclos `down`/`up`, `up --build` e depois `down -v`. Resultado esperado: `1` após os ciclos e o rebuild, e `0` após o `down -v` (SC-003)

**Checkpoint**: persistência comprovada; remoção só por comando explícito. Suíte verde.

---

## Phase 5: User Story 3 - Configuração por ambiente sem segredos no repositório (Priority: P2)

**Goal**: sobe sem `.env`; `.env` local sobrescreve padrões e nunca é versionado; a API recusa a chave padrão fora do modo de desenvolvimento; CORS fechado por padrão com origens extras por configuração.

**Independent Test**: quickstart V6 (passos 1–4 e 6) + testes de `validar_secret_key` e CORS verdes.

### Tests for User Story 3 ⚠️

- [ ] T031 [P] [US3] Adicionar em `backend/tests/config/test_env.py` os testes de `validar_secret_key(secret_key, debug)`:
  - com `debug=False` e `CHAVE_DEV_PADRAO`, lança `ImproperlyConfigured` cuja mensagem contém `DJANGO_SECRET_KEY`;
  - com `debug=False` e chave `""`, lança;
  - com `debug=False` e chave personalizada, não lança;
  - com `debug=True` e `CHAVE_DEV_PADRAO`, não lança.

  (FR-012, data-model §2)
- [ ] T032 [P] [US3] Escrever `backend/tests/core/test_cors.py`:
  - `GET /api/health/` com `HTTP_ORIGIN="http://site-externo.example"` retorna **sem** o cabeçalho `Access-Control-Allow-Origin`;
  - com `override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:3000"])` e `HTTP_ORIGIN="http://localhost:3000"`, o cabeçalho é `http://localhost:3000`.

  Rodar a suíte e confirmar a **falha** de T031 e T032 (FR-013, research R-06).

### Implementation for User Story 3

- [ ] T033 [US3] Implementar `validar_secret_key(secret_key, debug)` em `backend/config/env.py`. A função lança `ImproperlyConfigured("Defina a variável DJANGO_SECRET_KEY com uma chave própria: a chave padrão de desenvolvimento só é aceita com DJANGO_DEBUG=1.")` quando `not debug` e a chave está vazia ou é igual a `CHAVE_DEV_PADRAO` (research R-12)
- [ ] T034 [US3] Atualizar `backend/config/settings.py`:
  - chamar `validar_secret_key(SECRET_KEY, DEBUG)` logo após definir as duas variáveis;
  - adicionar `"corsheaders"` a `INSTALLED_APPS` e `"corsheaders.middleware.CorsMiddleware"` **antes** de `CommonMiddleware`;
  - definir `CORS_ALLOWED_ORIGINS = env_list("DJANGO_CORS_ALLOWED_ORIGINS")`.

  Rodar a suíte e confirmar T031 e T032 **verdes** (depende de T033).
- [ ] T035 [US3] Em `compose.yaml`, adicionar ao `backend` a variável `DJANGO_CORS_ALLOWED_ORIGINS: ${DJANGO_CORS_ALLOWED_ORIGINS:-}`. Conferir que todas as variáveis da tabela "Configuráveis" de [contracts/environment.md](contracts/environment.md) chegam ao compose com os padrões documentados (FR-009, FR-010)
- [ ] T036 [P] [US3] Criar `.env.example` na raiz com **todas** as 10 variáveis da tabela "Configuráveis" de [contracts/environment.md](contracts/environment.md): mesmos padrões e um comentário em pt-BR por variável. `DJANGO_SECRET_KEY` fica vazia, com o comentário "obrigatória se DJANGO_DEBUG=0". O comentário de `POSTGRES_PASSWORD` avisa que ela só vale ao inicializar um volume vazio. O comentário de `DJANGO_ALLOWED_HOSTS` avisa que um valor personalizado MUST incluir `localhost` e `backend` (ex.: `localhost,backend,192.168.0.10`) (FR-011, research R-05, R-07)
- [ ] T037 [US3] Rodar `docker compose run --rm backend pytest` (verde) e validar o cenário V6 do [quickstart.md](quickstart.md), passos 1 a 4 e 6: sobe sem `.env`, `.env` sobrescreve padrões, `.env` ignorado pelo Git e `DJANGO_DEBUG=0` com a chave padrão falha citando `DJANGO_SECRET_KEY`. No passo 4, validar tanto `manage.py check` quanto a subida real da API (`docker compose run --rm -e DJANGO_DEBUG=0 backend`), que usa o comando padrão do serviço (US3, cenário 4)

**Checkpoint**: configuração por ambiente segura; CORS fechado por padrão. Suíte verde.

---

## Phase 6: User Story 4 - Estrutura do banco e testes sem passos manuais (Priority: P2)

**Goal**: migrations rodam sozinhas a cada subida, antes de a API aceitar requisições; a suíte roda com um comando sem tocar nos dados reais.

**Independent Test**: `down -v` + `up` mostra migrations aplicadas antes do servidor; segunda subida sem erro; quickstart V7.

### Tests for User Story 4 ⚠️

- [ ] T038 [P] [US4] **Teste de guarda. Não há implementação associada, então o ciclo Red-Green do Princípio IV não se aplica.** Escrever `backend/tests/test_migrations.py`, que chama `call_command("makemigrations", "--check", "--dry-run")` dentro de `@pytest.mark.django_db` e espera que **não** haja `SystemExit` (sem migrations pendentes, Definition of Done da constituição). Rodar a suíte: esperado **verde** já neste ponto. O teste protege as specs futuras contra models alterados sem migration

### Implementation for User Story 4

- [ ] T039 [US4] Criar `backend/scripts/start-dev.sh` (LF, `#!/bin/sh`, `set -e`), que roda `python manage.py migrate --noinput` e depois `exec python manage.py runserver 0.0.0.0:8000` (FR-004, research R-04)
- [ ] T040 [US4] Trocar o comando do backend para `["sh", "scripts/start-dev.sh"]` em `compose.yaml` (`command:` do serviço `backend`) e no `CMD` de `backend/Dockerfile`. Assim o `docker compose run --rm backend pytest` continua **sem** migrar o banco real (depende de T039)
- [ ] T041 [US4] Validar:
  - `docker compose down -v` e depois `docker compose up -d --wait`: em `docker compose logs backend`, as migrations `auth`/`contenttypes` aparecem antes de "Starting development server" (quickstart V1, passo 4);
  - `docker compose restart backend` sobe sem erro e sem alterar dados (US4, cenário 2);
  - o cenário V7 do [quickstart.md](quickstart.md): suíte verde e registro real intocado.

**Checkpoint**: estrutura do banco e testes totalmente automáticos. Suíte verde.

---

## Phase 7: User Story 5 - Documentação de uso do ambiente (Priority: P3)

**Goal**: qualquer pessoa sobe, acessa (inclusive pelo celular), para, testa, configura e remove os dados só lendo o README.

**Independent Test**: quickstart V10.

### Implementation for User Story 5

- [ ] T042 [US5] Reescrever `README.md` em pt-BR, com as seções:
  1. O que é o Grana.io.
  2. Pré-requisitos (só Docker com Compose v2, em execução).
  3. Subir: `docker compose up` e `docker compose up -d --wait`. Reconstruir após mudar dependências: `docker compose up --build -V`, explicando que o `-V` descarta o `node_modules` antigo do frontend sem tocar nos dados do banco ([contracts/commands.md](contracts/commands.md)).
  4. Acessar: tabela de URLs da interface, da API e da saúde, segundo [contracts/commands.md](contracts/commands.md).
  5. Acessar pela rede local:
     - descobrir o IP (`ipconfig` / `ip addr`);
     - abrir `http://<IP>:5173`, **pelo IP**, porque nomes de host como `meu-pc.local` são bloqueados pelo Vite ("Blocked request. This host is not allowed");
     - liberar as portas TCP 5173 e 8000 no firewall, só no perfil de rede **privada**;
     - aviso de que expor à internet não é suportado.
  6. Parar: `docker compose down`.
  7. Rodar os testes: `docker compose run --rm backend pytest`.
  8. Personalizar a configuração: `.env.example` → `.env`. Incluir o aviso sobre `POSTGRES_PASSWORD` e o volume já inicializado, e o aviso de que um `DJANGO_ALLOWED_HOSTS` personalizado precisa incluir `localhost` e `backend`.
  9. Remover os dados locais: `docker compose down -v`, com aviso de **irreversível**.
  10. Solução de problemas: Docker parado, porta ocupada (`FRONTEND_PORT`/`BACKEND_PORT`), "API inacessível" (incluindo a causa `DJANGO_ALLOWED_HOSTS` sem `localhost`/`backend`), "banco indisponível", "Blocked request" ao acessar por nome de host, e dependências desatualizadas após rebuild (usar `-V`).
  11. Link para `docs/arquitetura.md` e `BACKLOG.md`.

  (FR-017)
- [ ] T043 [US5] Validar o cenário V10 do [quickstart.md](quickstart.md): percorrer o README do zero, num clone limpo, executando só o que está escrito, e corrigir qualquer lacuna encontrada (SC-006)

**Checkpoint**: README autossuficiente.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: verificações transversais e encerramento da Definition of Done

- [ ] T044 Rodar `git add --renormalize .` e conferir com `git ls-files --eol` que `*.sh`, `Dockerfile`, `compose.yaml`, `.env.example` e os demais textos estão como `i/lf` (quickstart V9, passo 1; FR-016)
- [ ] T045 [P] Rodar a busca de segredos do cenário V6, passo 5 (`git grep -nIiE "(password|secret|token|api[_-]?key)\s*[:=]"`) e confirmar que só aparecem valores de desenvolvimento claramente identificados e leituras de ambiente (SC-004)
- [ ] T046 Executar o [quickstart.md](quickstart.md) completo (V1 a V10) no Windows, num clone limpo, cronometrando a primeira subida (≤ 10 min, SC-001) e uma subida seguinte (≤ 1 min, SC-002)
- [ ] T047 Executar V1, V2 e V7 num host Linux ou no WSL2 com Docker Engine e confirmar resultado idêntico ao do Windows (SC-007)
- [ ] T048 Fechar a Definition of Done:
  - `docker compose run --rm backend pytest` verde;
  - todas as tarefas deste arquivo marcadas;
  - em `BACKLOG.md`, marcar como atendidos os critérios do RNF-01 e os critérios de infraestrutura do RNF-02 ("O CORS é restrito à origem do frontend" e "Nenhum segredo fica versionado no repositório").

**Checkpoint**: feature pronta para PR na `main`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: depende do Setup e **bloqueia** todas as histórias, porque sem ela não há suíte para o test-first.
- **US1 (Phase 3)**: depende só da Foundational.
- **US2 (Phase 4)**: depende da Foundational. Na prática é validada com a US1 no ar, mas só altera o `db` no `compose.yaml`.
- **US3 (Phase 5)**: depende da Foundational. O teste de CORS (T032) usa `/api/health/`, portanto depende da US1.
- **US4 (Phase 6)**: depende da Foundational. A validação T041 usa a US1 no ar.
- **US5 (Phase 7)**: depende de US1 a US4, porque documenta os comandos finais.
- **Polish (Phase 8)**: depende de todas as histórias.

### User Story Dependencies

```text
Setup → Foundational → US1 ─┬→ US2 ─┐
                            ├→ US3 ─┼→ US5 → Polish
                            └→ US4 ─┘
```

### Within Each User Story

- Testes escritos e **falhando** antes da implementação (Princípio IV).
- Service antes da view; view antes da rota; cliente de API → função de recurso → hook → página.
- `compose.yaml` é editado por várias fases (T011, T027, T029, T035 e T040), sempre de forma
  sequencial, nunca em paralelo.

### Parallel Opportunities

- Setup: T001 a T009 são todos [P] (arquivos distintos). T010 espera T007.
- US1: T018 ∥ T019 (testes). T023 (frontend) pode andar em paralelo com T020 a T022 (backend).
- US3: T031 ∥ T032 (testes). T036 (`.env.example`) ∥ T033 e T034.
- US4: T038 ∥ T039.
- Polish: T045 ∥ T044.

---

## Parallel Example: User Story 1

```bash
# Testes do backend juntos (arquivos distintos):
Task: "T018 Testes de verificar_banco() em backend/tests/core/test_saude_service.py"
Task: "T019 Testes de GET /api/health/ em backend/tests/core/test_health.py"

# Backend e frontend em paralelo depois dos testes:
Task: "T020–T022 Service, view e rota de saúde em backend/core/"
Task: "T023 Cliente de API em frontend/src/api/client.js"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 (Setup) → Phase 2 (Foundational): suíte rodando no Docker.
2. Phase 3 (US1): sistema sobe com um comando, saúde e página inicial.
3. **Parar e validar** pelo quickstart V1 a V4 (demonstrável no PC e no celular).

### Incremental Delivery

1. Setup + Foundational → base testável.
2. US1 → MVP demonstrável.
3. US2 → dados persistentes (pré-requisito para qualquer uso real).
4. US3 → configuração segura (fecha a parte de infraestrutura do RNF-02).
5. US4 → migrations automáticas e testes isolados.
6. US5 → README.
7. Polish → Definition of Done e PR.

---

## Notes

- [P] = arquivos diferentes, sem dependência pendente.
- Rótulos [USx] rastreiam cada tarefa até a história da spec.
- Dockerfiles, compose, settings, scripts e frontend provisório são glue, validados pelo quickstart (Princípio IV).
- Pare em cada **Checkpoint** com a suíte verde, apresente o resumo e sugira o commit.
- Commits manuais, em pt-BR, no padrão Conventional Commits, **sem** `Co-Authored-By` nem rodapés de IA.

**Commit recomendado após cada checkpoint (T010, T017, T028, T030, T037, T041, T043, T048)**:

| Checkpoint | Mensagem sugerida |
|---|---|
| T010 | `chore: cria esqueleto do backend Django e do frontend React com Dockerfiles` |
| T017 | `feat: configura compose com banco e backend, settings por ambiente e suíte pytest` |
| T028 | `feat: adiciona verificação de saúde da API e página inicial com proxy do Vite (US1)` |
| T030 | `feat: persiste dados do banco em volume nomeado (US2)` |
| T037 | `feat: bloqueia chave secreta padrão fora do modo dev e restringe CORS (US3)` |
| T041 | `feat: aplica migrations automaticamente na subida do backend (US4)` |
| T043 | `docs: documenta subida, acesso pela rede, testes e remoção de dados no README (US5)` |
| T048 | `chore: normaliza finais de linha e conclui RNF-01` |
