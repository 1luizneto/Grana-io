# Implementation Plan: Execução Local com Um Comando (Infraestrutura Docker)

**Branch**: `001-infra-docker` | **Date**: 2026-09-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-infra-docker/spec.md`

**Backlog**: RNF-01 (integral) + parte de infraestrutura do RNF-02 (segredos por ambiente, CORS
restrito, permissão padrão autenticada).

## Summary

Um único `docker compose up` sobe três serviços: `db` (PostgreSQL 17 com volume nomeado),
`backend` (Django 5.2 + DRF, que espera o banco saudável, roda `migrate` e inicia o `runserver`)
e `frontend` (React + Vite em modo dev). Toda configuração vem de variáveis de ambiente, com
padrões de desenvolvimento embutidos no `compose.yaml`, de modo que o `.env` é opcional, não é
versionado e é documentado pelo `.env.example`.

A interface chama a API por caminho relativo `/api`, e o Vite faz proxy para o backend. Por isso
o acesso funciona por `localhost` e pelo IP da rede local sem configuração nem rebuild, e o CORS
não precisa liberar nenhuma origem por padrão. A API expõe só a verificação de saúde pública
`GET /api/health/`, e a página inicial provisória mostra o estado dela. A suíte roda com
`docker compose run --rm backend pytest`, num banco de teste separado. Detalhes e alternativas
estão em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (backend); JavaScript/JSX em Node 24 LTS (frontend) — [R-01](research.md), [R-16](research.md)

**Primary Dependencies**: Django 5.2 LTS, Django REST Framework, psycopg 3 (binary),
django-cors-headers; React 19, Vite (+ @vitejs/plugin-react) — justificativas em [R-15](research.md)

**Storage**: PostgreSQL 17 (`postgres:17-alpine`), com volume Docker nomeado `grana_pgdata` e sem
porta exposta — [R-05](research.md)

**Testing**: pytest + pytest-django no container do backend, usando o banco temporário
`test_grana`. Frontend sem framework de testes nesta spec — [R-13](research.md), [R-14](research.md)

**Target Platform**: Docker Desktop (Windows 11) e Docker Engine + Compose v2 (Linux). Navegadores
modernos no desktop e no celular pela rede local.

**Project Type**: aplicação web (backend API REST + frontend SPA) orquestrada por Docker Compose

**Performance Goals**: primeira subida ≤ 10 min, incluindo downloads (SC-001); subidas seguintes
≤ 1 min (SC-002)

**Constraints**: nenhuma dependência na máquina além do Docker; banco inacessível fora do Compose
(FR-019); recarga automática sem rebuild (FR-015); LF em arquivos de texto (FR-016); nenhum dado
enviado a serviços externos (Princípio I)

**Scale/Scope**: uso local por 1 a 3 usuários numa rede doméstica. Esta spec entrega só o
esqueleto: 1 endpoint e 1 página.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Princípio / regra | Avaliação pré-pesquisa | Pós-design |
|---|---|---|---|
| I | Localidade e privacidade | Postgres local em Docker. Segredos só por ambiente, `.env` ignorado e `.env.example` versionado. Nenhum serviço externo. | ✅ `contracts/environment.md` define as variáveis. A resposta de saúde não expõe detalhes internos (`contracts/api-health.md`). O banco não tem porta publicada. |
| II | Isolamento por usuário | N/A: sem registros de domínio nesta spec. | ✅ Permissão global `IsAuthenticated` configurada. Rotas futuras nascem protegidas, e só `/api/health/` é `AllowAny` ([R-11](research.md)). |
| III | Precisão monetária | N/A: sem valores monetários. | ✅ N/A |
| IV | Testes obrigatórios (test-first) | Os testes do endpoint de saúde e do bloqueio da chave secreta são escritos antes. A suíte roda com 1 comando no Docker. O glue é validado pelo quickstart. | ✅ `docker compose run --rm backend pytest` ([R-13](research.md)). Quickstart V1 a V10 cobre o glue. |
| V | Separação backend/frontend | Comunicação só por REST, com contrato em `contracts/`. URL da API configurável. Frontend sem regra de negócio. | ✅ Cliente de API central em `src/api/`, com `VITE_API_URL` opcional e proxy `/api` como padrão ([R-06](research.md)). |
| VI | Simplicidade / incremental | Corresponde a RNF-01 e parte do RNF-02. Deps justificadas. Sem abstrações especulativas. | ✅ Sem framework de testes no frontend, sem TypeScript, sem middleware de hosts e sem override de compose ([R-14](research.md), [R-16](research.md), [R-07](research.md), [R-02](research.md)). |
| — | Stack & constraints | Python 3.12+, Django 5.2, DRF, React/Vite, PostgreSQL em Docker, Compose, pytest. Localização pt-BR e fuso `America/Sao_Paulo`. | ✅ `LANGUAGE_CODE=pt-br`, `TIME_ZONE=America/Sao_Paulo`, `USE_TZ=True`. JWT fica para a US-02 (fora do escopo). |
| — | `docs/arquitetura.md` | App `core` para itens transversais, views finas e service para a checagem do banco. Frontend com `api/`, `hooks/`, `pages/`. | ✅ `core/services/saude.py` + `HealthView` fina. `useSaudeApi()` → `api/saude.js` → `api/client.js`. Página em `pages/Inicio/`. |
| — | Workflow | Branch `001-infra-docker` = diretório da spec. Commits manuais sem trailer de IA. | ✅ |

**Resultado**: nenhuma violação e nada a registrar em Complexity Tracking. O gate passou antes da
Phase 0 e foi reconfirmado após a Phase 1.

**Riscos aceitos (não são violações)**: `DJANGO_ALLOWED_HOSTS=*` e páginas de erro detalhadas
visíveis na rede local enquanto só existe o modo de desenvolvimento ([R-07](research.md), Assumptions
da spec). Os dois são mitigados pelo RNF-09 antes de lançar dados reais.

## Project Structure

### Documentation (this feature)

```text
specs/001-infra-docker/
├── plan.md              # Este arquivo
├── research.md          # Phase 0: decisões técnicas (R-01 a R-17)
├── data-model.md        # Phase 1: volume, configuração e resposta de saúde
├── quickstart.md        # Phase 1: roteiro de validação V1 a V10
├── contracts/
│   ├── api-health.md    # GET /api/health/
│   ├── environment.md   # Variáveis de ambiente
│   └── commands.md      # Comandos operacionais e endereços
├── checklists/
│   └── requirements.md  # (gerado no /speckit-specify)
└── tasks.md             # Phase 2 (/speckit-tasks; NÃO criado por este comando)
```

### Source Code (repository root)

```text
compose.yaml                 # db, backend, frontend; name: grana; volume pgdata
.env.example                 # todas as variáveis configuráveis, com padrões de dev
.gitignore                   # .env, node_modules, __pycache__, .pytest_cache, etc.
.gitattributes               # * text=auto eol=lf (FR-016)
README.md                    # subir, parar, acessar (local e rede), testar, configurar, remover dados

backend/
├── Dockerfile               # python:3.12-slim; instala requirements-dev.txt
├── .dockerignore
├── requirements.txt         # Django, DRF, psycopg[binary], django-cors-headers (versões fixas)
├── requirements-dev.txt     # -r requirements.txt + pytest, pytest-django
├── pytest.ini               # DJANGO_SETTINGS_MODULE=config.settings
├── manage.py
├── scripts/
│   └── start-dev.sh         # migrate --noinput && exec runserver 0.0.0.0:8000
├── config/
│   ├── __init__.py
│   ├── env.py               # env_str/env_bool/env_list, CHAVE_DEV_PADRAO, validar_secret_key()
│   ├── settings.py          # 12-factor; DRF IsAuthenticated global; CORS; pt-BR; America/Sao_Paulo
│   ├── urls.py              # /api/ → core.urls
│   ├── wsgi.py
│   └── asgi.py
├── core/
│   ├── __init__.py
│   ├── apps.py
│   ├── urls.py              # health/
│   ├── views.py             # HealthView (APIView, AllowAny, só GET)
│   └── services/
│       ├── __init__.py
│       └── saude.py         # verificar_banco() -> bool
└── tests/
    ├── conftest.py
    ├── config/
    │   └── test_env.py      # helpers de env + bloqueio da chave secreta (FR-012)
    └── core/
        └── test_health.py   # 200, 503 sem detalhes, anônimo permitido, 405 em POST (FR-007)

frontend/
├── Dockerfile               # node:24-alpine; npm ci; vite --host
├── .dockerignore
├── package.json
├── package-lock.json        # gerado dentro do container
├── vite.config.js           # host: true; watch.usePolling; proxy /api → API_PROXY_TARGET
├── index.html
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── api/
    │   ├── client.js        # base = VITE_API_URL ?? '' ; requisições centralizadas
    │   └── saude.js         # obterSaude()
    ├── hooks/
    │   └── useSaudeApi.js   # estados: carregando | ok | banco-indisponivel | inacessivel
    └── pages/
        └── Inicio/
            └── Inicio.jsx   # nome do sistema + estado da API
```

**Structure Decision**: aplicação web com `backend/` e `frontend/` na raiz, seguindo
`docs/arquitetura.md` §2.3 e §3. O app `core` recebe o que é transversal (hoje, a saúde; depois,
`OwnedModel`, mixins e o helper monetário). Os testes do backend espelham os apps em
`backend/tests/<app>/`. `compose.yaml`, `.env.example`, `.gitattributes` e `.gitignore` ficam na
raiz do repositório.

## Complexity Tracking

Nenhuma violação da constituição ou de `docs/arquitetura.md`. Nada a justificar.

## Pontos para revisão do responsável

Estas decisões seguem o YAGNI, mas mudam o formato das próximas specs. Vale confirmá-las antes do
`/speckit-tasks`:

1. **Sem testes de frontend nesta spec** ([R-14](research.md)): o Vitest entra na US-26. Até lá,
   "a suíte com 1 comando" é só a do backend.
2. **JavaScript em vez de TypeScript** no frontend ([R-16](research.md)).
3. **Proxy do Vite como forma padrão de chegar à API** ([R-06](research.md)): para o RNF-09 (modo de
   uso), isso implica servir o build atrás de um proxy equivalente (ex.: nginx), a ser planejado
   naquela spec.
