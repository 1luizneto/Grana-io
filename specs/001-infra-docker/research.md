# Research: Execução Local com Um Comando (Infraestrutura Docker)

**Feature**: `001-infra-docker` | **Data**: 2026-09-25 | **Plano**: [plan.md](plan.md)

Este documento resolve as decisões técnicas do Technical Context. Não restou nenhum
"NEEDS CLARIFICATION".

---

## R-01 — Versões de runtime e imagens base

- **Decision**: `python:3.12-slim` (backend), `node:24-alpine` (frontend), `postgres:17-alpine` (banco).
- **Rationale**: Python 3.12 é a versão mínima da constituição e é suportada pelo Django 5.2 LTS.
  Node 24 é a LTS ativa e atende ao requisito de Node do Vite atual. PostgreSQL 17 é estável,
  suportado pelo Django 5.2 (mínimo PG 14) e mantém o layout de volume clássico
  (`/var/lib/postgresql/data`). Imagens `slim`/`alpine` reduzem o download da primeira subida (SC-001).
- **Alternatives considered**:
  - `postgres:18`: a imagem mudou o diretório de dados recomendado para `/var/lib/postgresql`, o que
    exige mais cuidado com o volume e não traz nada de que o projeto precise agora.
  - `python:3.13`: também é suportado, mas não há ganho concreto, e 3.12 é a base declarada na constituição.
  - Imagens `alpine` para Python: o `psycopg[binary]` e outras wheels funcionam melhor em glibc (`slim`).

## R-02 — Arquivo do Compose e nome do projeto

- **Decision**: um único `compose.yaml` na raiz, com `name: grana`. Os serviços são `db`, `backend` e `frontend`.
- **Rationale**: `compose.yaml` é o nome canônico do Compose v2, e `docker compose up` o encontra
  sem precisar de flag. Fixar `name: grana` torna o nome do volume previsível (`grana_pgdata`),
  qualquer que seja o nome da pasta clonada, e facilita documentar a remoção dos dados.
- **Alternatives considered**: um `docker-compose.yml` com override para dev ficou para depois. Hoje só
  existe o modo de desenvolvimento (clarificação 2), e o modo de uso (RNF-09) vai decidir entre
  override e profile quando for especificado.

## R-03 — Valores padrão sem arquivo `.env` (FR-009, FR-010, FR-011)

- **Decision**: os valores padrão de desenvolvimento ficam na interpolação do próprio `compose.yaml`
  (`${VAR:-padrão}`). O Compose lê automaticamente o `.env` da raiz, quando ele existe, e seus
  valores prevalecem. O `.env.example` é versionado e lista todas as variáveis com os mesmos padrões
  e comentários. O `.env` fica no `.gitignore`.
- **Rationale**: atende ao FR-010 sem exigir `cp .env.example .env` e sem depender de
  `env_file: required: false`, que exige Compose ≥ 2.24. Todo padrão fica num lugar só (o compose),
  e o `.env.example` é a documentação dele.
- **Exceção — `DJANGO_SECRET_KEY`**: o compose repassa `${DJANGO_SECRET_KEY:-}` (vazio se não
  definida). O padrão de desenvolvimento fica numa constante do `config/env.py`, e é ela que o
  bloqueio do FR-012 compara. Assim o valor padrão existe em um único lugar do código.
- **Alternatives considered**: `django-environ` / `python-decouple` foram descartados. Três helpers
  pequenos (`env_str`, `env_bool`, `env_list`) cobrem a necessidade sem acrescentar dependência (Princípio VI).

## R-04 — Espera pelo banco e migrations automáticas (FR-003, FR-004)

- **Decision**:
  - O serviço `db` tem um healthcheck com `pg_isready`, e o `backend` usa
    `depends_on: db: condition: service_healthy`.
  - O comando padrão do `backend` é `sh scripts/start-dev.sh`, que roda `migrate --noinput` e depois
    `exec runserver 0.0.0.0:8000`.
- **Rationale**: o healthcheck nativo resolve a espera sem script de "wait-for". `migrate` é
  idempotente (US4, cenário 2) e roda antes de a API aceitar conexões. Como a migração está no
  **comando** (e não no entrypoint da imagem), `docker compose run --rm backend pytest` substitui o
  comando e **não** migra o banco real ao rodar testes (US4, cenário 4).
- O script é chamado com `sh` explícito, então funciona mesmo sem bit de execução (checkout no Windows).
- **Alternatives considered**: um entrypoint que sempre migra foi descartado porque rodaria contra o
  banco real também em `run pytest`. Um serviço `migrate` separado adicionaria um container de vida
  curta sem necessidade.

## R-05 — Persistência e remoção dos dados (FR-005, FR-006, FR-019)

- **Decision**: volume nomeado `pgdata` (resolvido como `grana_pgdata`) montado em
  `/var/lib/postgresql/data`. A remoção explícita é feita com `docker compose down -v`. O `db` não
  tem `ports:` e só é acessível pela rede interna do Compose.
- **Rationale**: volumes nomeados sobrevivem a `down`, `restart`, reboot e `build`. Só `-v` (ou
  `docker volume rm`) os apaga, o que atende a "nenhuma outra operação rotineira pode apagá-los".
  Sem `ports:`, o PostgreSQL não fica exposto nem no host nem na rede local (FR-019).
- **Atenção documentada**: a imagem do PostgreSQL só aplica `POSTGRES_PASSWORD` na **inicialização
  de um volume vazio**. Se a senha mudar no `.env` depois da primeira subida, a conexão falha. O
  README e o quickstart orientam a trocar a senha antes da primeira subida, ou a rodar `down -v`
  (apagando os dados) para reinicializar.
- **Alternatives considered**: um bind mount (`./data/pg`) foi descartado. No Windows ele sofre com
  permissões e desempenho, e ainda arrisca ser versionado por engano.

## R-06 — Como a interface encontra a API, local e pela rede (FR-008, FR-013, FR-018)

- **Decision**: o frontend chama a API por caminho **relativo** (`/api/...`), e o servidor de
  desenvolvimento do Vite faz **proxy** de `/api` para `http://backend:8000`, na rede interna do
  Compose. Se `VITE_API_URL` estiver definida, o cliente de API usa essa URL absoluta.
- **Rationale**:
  - O navegador (PC ou celular) sempre chama o mesmo host e a mesma porta de onde abriu a interface.
    Por isso funciona por `localhost`, pelo IP da rede e após troca de IP, sem rebuild nem configuração
    (FR-018, edge case "IP da máquina muda"). Também elimina o problema de "localhost no celular".
  - As requisições da própria interface são *same-origin*, então o CORS não precisa liberar
    nenhuma origem por padrão. O `django-cors-headers` fica configurado com lista **vazia**, e origens
    extras só entram por `DJANGO_CORS_ALLOWED_ORIGINS` (FR-013). Um site de terceiros aberto no
    navegador não consegue ler respostas da API.
  - `VITE_API_URL` mantém a URL da API configurável por ambiente (Princípio V, RNF-08).
- **Alternatives considered**: a chamada direta do navegador para `http://<host>:8000` foi descartada.
  Ela exigiria injetar o IP da máquina na build, que quebra quando o IP muda, ou calcular o host em
  runtime com CORS aceitando `http://<qualquer-host>:5173`. Essa regra de CORS seria permissiva demais
  e dependeria da porta, que é configurável.

## R-07 — Hosts aceitos pelo Django e pelo Vite na rede local

- **Decision**: `DJANGO_ALLOWED_HOSTS` tem padrão `*` no modo de desenvolvimento e é configurável
  pelo `.env`. No Vite, `server.host: true` (escuta em `0.0.0.0` dentro do container). Não é preciso
  mexer em `server.allowedHosts`, porque o Vite já aceita `localhost` e endereços IP por padrão.
- **Rationale**: o FR-018 exige acesso pelo IP da máquina sem reconfigurar quando o IP muda. O
  Django não aceita faixas de IP em `ALLOWED_HOSTS`, então a alternativa seria um middleware próprio
  (desnecessário agora). Com rede doméstica confiável e sem dados reais (Assumptions da spec), o risco
  de *Host header poisoning* é aceitável no modo de desenvolvimento. O RNF-09 (modo de uso) deve exigir
  hosts explícitos.
- **Consequência**: se `DJANGO_ALLOWED_HOSTS` for personalizada, ela precisa incluir `localhost`
  (healthcheck do container) e `backend` (o proxy do Vite usa `changeOrigin: true` e envia
  `Host: backend:8000`). Caso contrário, o container fica unhealthy e a interface mostra "API
  inacessível". Isso está documentado em `contracts/environment.md`, no `.env.example` e no README.
- **Hostnames no Vite**: o Vite aceita `localhost` e IPs, mas bloqueia nomes de host
  (ex.: `meu-pc.local`) com "Blocked request. This host is not allowed". O acesso suportado pela
  rede é pelo IP, como diz a spec, e o README avisa sobre isso.
- **Alternatives considered**: um middleware que aceita faixas privadas (RFC 1918) seria complexidade
  especulativa, adiada para o RNF-09 se necessário.

## R-08 — Portas e exposição na rede (FR-018, FR-019, edge case "porta ocupada")

- **Decision**: `"${FRONTEND_PORT:-5173}:5173"` e `"${BACKEND_PORT:-8000}:8000"`. O bind padrão do
  Docker é `0.0.0.0` e, com isso, as portas ficam acessíveis na rede local. Dentro dos containers
  as portas são fixas (5173 e 8000); só a porta do host é configurável.
- **Rationale**: trocar a porta do host resolve o conflito "porta já ocupada" sem mexer em código.
  Como o proxy aponta para a porta interna fixa, mudar `BACKEND_PORT` não afeta a interface.
- **Firewall**: no Windows, o Docker Desktop costuma pedir permissão na primeira publicação de
  porta. O README orienta a liberar as portas 5173 e 8000 no perfil de **rede privada**.

## R-09 — Recarga automática sem rebuild (FR-015) e compatibilidade com Windows

- **Decision**:
  - `./backend:/app` e `./frontend/src:/app/src` como bind mounts. No frontend, só o código-fonte é
    montado, e o `node_modules` continua o da imagem, sem nenhum volume.
  - *Revisado na implementação (US2, 2026-09-30)*: o desenho original montava `./frontend:/app`
    com um volume anônimo em `/app/node_modules`. Isso vazava um volume órfão de ~44 MB a cada
    `down`/`up` e exigia `up --build -V` para não subir com dependências antigas. Montar só `src/`
    elimina os dois problemas. A contrapartida é que mudanças em `index.html`, `vite.config.js` ou
    `package.json` pedem `docker compose up --build`.
  - Django: `runserver` com o `StatReloader` padrão (polling), que funciona com bind mounts no Windows.
  - Vite: `server.watch.usePolling: true`, porque os eventos de arquivo do Windows não chegam ao
    container de forma confiável.
- **Rationale**: é o mínimo para refletir alterações sem `docker compose build`. Polling tem custo de
  CPU baixo para o tamanho do projeto.
- **Alternatives considered**: `docker compose watch` (`develop.watch`) foi descartado porque exige
  outro comando além de `docker compose up` e sincroniza por cópia, o que não traz vantagem aqui.

## R-10 — Final de linha LF (FR-016)

- **Decision**: `.gitattributes` com `* text=auto eol=lf`, marcando binários comuns como `binary`.
- **Rationale**: scripts `.sh`, `Dockerfile` e arquivos lidos dentro dos containers Linux quebram com
  CRLF (lição do projeto edge-computing). Forçar LF em todo arquivo de texto é mais simples do que
  listar extensões, e não prejudica editores modernos no Windows.
- Na implementação, depois de criar o arquivo, rodar `git add --renormalize .` para normalizar o que
  já estiver versionado.

## R-11 — Verificação de saúde (FR-007)

- **Decision**: `GET /api/health/`, pública (`AllowAny`), implementada como `APIView` do DRF no app
  `core`. Ela delega a checagem a `core/services/saude.py::verificar_banco()`, que executa
  `SELECT 1` e captura só `django.db.Error`. Retorna 200 `{"status": "ok", "database": "ok"}` ou
  503 `{"status": "error", "database": "unavailable"}`, sem mensagens de exceção, host ou credenciais.
- **Rationale**: a view fica fina e o service pode ser testado sem HTTP (`docs/arquitetura.md` §2).
  O 503 permite que o healthcheck do container e a interface distingam "API no ar, banco fora".
- **Configuração global do DRF**: `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` desde já. Toda
  rota nova nasce protegida (RNF-02), e a de saúde declara `AllowAny` explicitamente.
- **Alternatives considered**: `JsonResponse` puro sem DRF foi descartado. O DRF é stack obrigatória
  e será usado na spec seguinte (US-01), e configurar a permissão global agora evita esquecer depois.

## R-12 — Bloqueio da chave secreta padrão (FR-012)

- **Decision**: `config/env.py` expõe `validar_secret_key(secret_key, debug)`, que lança
  `ImproperlyConfigured` quando `debug` é falso e a chave está vazia ou é igual à constante de
  desenvolvimento. A mensagem cita `DJANGO_SECRET_KEY`. `settings.py` chama a função ao carregar.
  O padrão de `DJANGO_DEBUG` no `settings.py` é **falso** (seguro), e é o compose que liga o modo de
  desenvolvimento (`${DJANGO_DEBUG:-1}`).
- **Rationale**: falhar no carregamento das settings bloqueia qualquer forma de subir a API
  (runserver, futuro gunicorn, manage.py), ao contrário de um *system check*, que o gunicorn não
  executa. Isolar a regra numa função permite testá-la unitariamente.

## R-13 — Testes isolados dos dados reais (FR-014, SC-005)

- **Decision**: `pytest` + `pytest-django` no backend, rodando com
  `docker compose run --rm backend pytest`. O pytest-django cria e destrói o banco `test_grana` no
  mesmo servidor PostgreSQL, sem tocar no banco `grana`. O usuário do banco é superusuário na imagem
  oficial, então tem permissão para criar esse banco.
- **Rationale**: é o comando citado no RNF-05. `run` não publica portas, então roda em paralelo com o
  sistema no ar, e não executa o `start-dev.sh`, então não migra o banco real (R-04).
- **Alternatives considered**: SQLite nos testes é permitido pela constituição fora do Docker, mas
  divergiria do PostgreSQL real. Foi descartado como padrão.

## R-14 — Testes do frontend nesta spec

- **Decision**: esta spec **não** introduz framework de testes no frontend. A página inicial
  provisória é validada pelo quickstart (código de glue, isento pelo Princípio IV). O Vitest e o
  Testing Library entram na primeira spec com lógica real de frontend (US-26 / `AuthProvider`,
  `RotaProtegida`). Nessa spec também será definida a forma de manter "a suíte completa com um
  único comando".
- **Rationale**: o Princípio IV define como core os models, serviços, endpoints, autenticação e
  isolamento, todos no backend. A página de saúde não tem regra testável além de exibir o retorno da
  API. Adicionar 3 ou 4 dependências de teste agora seria especulativo (Princípio VI).
- **Alternatives considered**: configurar o Vitest já agora foi descartado pelo motivo acima.
  **Ponto para revisão do responsável**, caso prefira o harness pronto desde a Sprint 1.

## R-15 — Dependências novas (Princípio VI)

| Dependência | Camada | Justificativa |
|---|---|---|
| Django 5.2 LTS | backend | Stack obrigatória (constituição). |
| djangorestframework | backend | Stack obrigatória; endpoint de saúde e permissão global padrão (R-11). |
| psycopg[binary] 3 | backend | Driver PostgreSQL recomendado pelo Django 5.2. |
| django-cors-headers | backend | FR-013 / RNF-02: CORS restrito, origens extras por configuração (R-06). |
| pytest, pytest-django | backend (dev) | Stack de testes obrigatória (constituição). |
| react, react-dom | frontend | Stack obrigatória. |
| vite, @vitejs/plugin-react | frontend (dev) | Stack obrigatória; servidor de desenvolvimento com proxy e recarga. |

As versões são fixadas em `requirements*.txt` (backend) e `package-lock.json` (frontend). O lockfile
é gerado dentro do container (`docker compose run --rm frontend npm install`), porque a máquina não
precisa ter Node.

## R-16 — Linguagem do frontend

- **Decision**: JavaScript (JSX), sem TypeScript nesta fase.
- **Rationale**: nem a constituição nem a arquitetura exigem TypeScript, e ele acrescentaria
  configuração e dependências sem necessidade presente. Se os contratos da API crescerem a ponto de
  justificar tipos, a adoção entra por spec própria, com registro no plano.
- **Alternatives considered**: TypeScript desde o início. **Ponto para revisão do responsável.**

## R-17 — Usuário dos containers

- **Decision**: no modo de desenvolvimento, os containers rodam com o usuário padrão da imagem.
- **Rationale**: com bind mounts, um usuário não-root gera conflito de UID/permissão, principalmente
  em Linux (arquivos criados por `makemigrations`). O risco é baixo porque é ambiente local de
  desenvolvimento. O modo de uso (RNF-09) deve rodar como não-root.
