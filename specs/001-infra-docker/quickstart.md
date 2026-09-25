# Quickstart de Validação: Execução Local com Um Comando

**Feature**: `001-infra-docker` | **Plano**: [plan.md](plan.md)

Este roteiro prova, de ponta a ponta, que a feature funciona. Ele valida também o código de
glue (Dockerfiles, compose, settings), que é isento de teste unitário pelo Princípio IV. Os
comandos e endereços seguem [contracts/commands.md](contracts/commands.md), e as variáveis seguem
[contracts/environment.md](contracts/environment.md).

## Pré-requisitos

- Docker Desktop (Windows) ou Docker Engine + Compose v2 (Linux), **em execução**.
- Git.
- Nenhuma outra instalação (Python, Node, PostgreSQL) é necessária.
- Portas 5173 e 8000 livres no host.
- Para o cenário V3: um celular na mesma rede Wi-Fi.

## Cenários

Execute na raiz do repositório, na ordem. Cada cenário indica o requisito que valida.

### V1 — Clone limpo sobe com um comando (US1; FR-001, FR-003, FR-004; SC-001)

1. Clone o repositório numa pasta nova, **sem** criar `.env`.
2. Rode `docker compose up -d --wait` e cronometre.
3. **Esperado**: o comando termina sem erro em até 10 min na primeira vez. `docker compose ps`
   mostra `db` e `backend` como `healthy` e `frontend` como `running`.
4. Rode `docker compose logs backend`. **Esperado**: as migrations aplicadas aparecem antes de
   "Starting development server", sem erro de conexão com o banco.

### V2 — Saúde da API e página inicial (US1; FR-007, FR-008)

1. Abra `http://localhost:8000/api/health/`. **Esperado**: HTTP 200 e corpo
   `{"status": "ok", "database": "ok"}` ([contrato](contracts/api-health.md)).
2. Abra `http://localhost:5173`. **Esperado**: a página exibe o nome "Grana.io" e informa que a
   API está acessível.
3. Abra `http://localhost:5173/api/health/`. **Esperado**: a mesma resposta do passo 1, porque
   passa pelo proxy da interface.

### V3 — Acesso pela rede local (US1 cenário 6; FR-018, FR-019; SC-008)

1. Descubra o IP da máquina (`ipconfig` no Windows ou `ip addr` no Linux).
2. No celular, abra `http://<IP>:5173`. **Esperado**: a página carrega e mostra a API acessível,
   sem configurar nada no celular.
3. No celular, abra `http://<IP>:8000/api/health/`. **Esperado**: HTTP 200.
4. De outro dispositivo (ou do próprio host), tente conectar em `<IP>:5432`. **Esperado**:
   conexão recusada, porque o banco não está exposto.
5. *(Opcional)* Troque o IP da máquina (reconectar/renovar DHCP) e repita o passo 2 com o novo IP,
   sem rebuild. **Esperado**: funciona.

### V4 — API espera o banco e trata a queda dele (US1 cenário 4; edge cases)

1. Rode `docker compose stop db` e então `curl -i http://localhost:8000/api/health/`.
   **Esperado**: HTTP 503, com corpo `{"status": "error", "database": "unavailable"}` e sem stack
   trace, host ou credenciais.
2. Abra `http://localhost:5173`. **Esperado**: a página informa que o banco está indisponível e
   não quebra.
3. Rode `docker compose stop backend`, recarregue a página. **Esperado**: "API inacessível", sem
   tela em branco.
4. Rode `docker compose up -d --wait`. **Esperado**: tudo volta a ficar saudável.

### V5 — Persistência e remoção explícita (US2; FR-005, FR-006; SC-003)

1. Grave um registro:
   `docker compose exec backend python manage.py shell -c "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='persistencia-teste')"`
2. Repita 5 vezes: `docker compose down` seguido de `docker compose up -d --wait`.
3. Rode `docker compose up -d --build --wait` (reconstrói as imagens da API e da interface).
4. Consulte:
   `docker compose exec backend python manage.py shell -c "from django.contrib.auth.models import Group; print(Group.objects.filter(name='persistencia-teste').count())"`
   **Esperado**: `1`.
5. Rode `docker compose down -v` e depois `docker compose up -d --wait`, e repita a consulta.
   **Esperado**: `0` (banco recriado vazio).

### V6 — Configuração por ambiente (US3; FR-009 a FR-012; SC-004)

1. **Sem `.env`**: coberto por V1.
2. **Com `.env`**: `docker compose down -v`. Copie `.env.example` para `.env` e troque
   `POSTGRES_PASSWORD` e `FRONTEND_PORT=5174`. Rode `docker compose up -d --wait`.
   **Esperado**: sobe normalmente, e a interface responde em `http://localhost:5174`.
   *(O `down -v` é necessário porque a senha só vale ao inicializar um volume vazio. Veja
   [research R-05](research.md).)*
3. **`.env` ignorado**: `git status --short` não lista `.env`, e `git check-ignore .env` imprime `.env`.
4. **Chave padrão fora do modo de dev**:
   `docker compose run --rm -e DJANGO_DEBUG=0 backend python manage.py check`
   **Esperado**: falha com erro de configuração citando `DJANGO_SECRET_KEY`.
5. **Sem segredos versionados**:
   `git grep -nIiE "(password|secret|token|api[_-]?key)\s*[:=]"`.
   **Esperado**: só aparecem valores de exemplo claramente de desenvolvimento (`dev`/`insecure`) e
   leituras de variáveis de ambiente.
6. Apague o `.env` e rode `docker compose down -v` para voltar ao padrão.

### V7 — Testes com um comando, isolados (US4; FR-014; SC-005)

1. Com o sistema no ar e o registro de V5 recriado (passo 1 de V5), rode
   `docker compose run --rm backend pytest`.
   **Esperado**: a suíte executa e termina com todos os testes aprovados (inclui os testes do
   endpoint de saúde e do bloqueio da chave secreta).
2. Repita a consulta do passo 4 de V5. **Esperado**: `1`, porque os testes não tocaram no banco real.

### V8 — Recarga sem rebuild (FR-015)

1. Com o sistema no ar, altere o texto da página inicial em `frontend/src/`. **Esperado**: o
   navegador reflete a mudança sem `docker compose build`.
2. Altere um arquivo Python do backend, por exemplo acrescentando um comentário em
   `core/views.py`. **Esperado**: `docker compose logs backend` mostra o reload automático.

### V9 — Finais de linha e Windows/Linux (FR-016; SC-007)

1. `git ls-files --eol` mostra `i/lf` para `*.sh`, `Dockerfile`, `compose.yaml` e demais textos.
2. Execute V1 e V2 num host Windows **e** num host Linux (ou WSL2 com Docker Engine).
   **Esperado**: resultado idêntico.

### V10 — README autossuficiente (US5; FR-017; SC-006)

1. Uma pessoa que não conhece o projeto segue **somente** o README para subir, acessar (incluindo
   pelo celular), parar, rodar os testes e remover os dados.
   **Esperado**: completa todas as operações na primeira tentativa, sem consultar outra fonte.

## Critério de encerramento

A feature está validada quando V1 a V10 passam e a suíte (V7) está verde.
