# Research: Modo de Uso

**Feature**: `011-modo-de-uso` | **Plano**: [plan.md](plan.md)

Fecha as pendências que a spec 001 deixou para o RNF-09 (research R-03, R-06, R-17 e a T008).

---

## R-01 — Um arquivo de sobreposição: `compose.uso.yaml`

**Decisão**: o modo de desenvolvimento continua sendo `compose.yaml`. O modo de uso é
`docker compose -f compose.yaml -f compose.uso.yaml up -d --build --wait`, com o arquivo de
sobreposição trocando só o que muda: alvo de build, imagem, comando, variáveis, portas e volumes
(`!reset` do Compose para tirar o código montado e a porta da API). Mesmo nome de projeto
(`grana`) e mesmo volume (`grana_pgdata`): os dois modos usam o mesmo banco (FR-006).

**Imagens com nomes próprios** (`grana-backend-uso`, `grana-frontend-uso`): voltar ao modo de
desenvolvimento não exige reconstruir (as imagens de desenvolvimento continuam lá).

**Alternativas**: um segundo arquivo completo (duplicaria o banco e as variáveis); perfis do
Compose (os dois modos teriam serviços com nomes diferentes, e trocar de modo deixaria containers
órfãos).

---

## R-02 — API: Gunicorn, sem root, sem código montado

**Decisão**: o `backend/Dockerfile` ganha estágios `dev` (o atual) e `uso`: `requirements.txt` +
`gunicorn==23.0.0`, código copiado na imagem, usuário `grana` sem privilégios, e o script
`scripts/start-uso.sh` (aplica as migrations e sobe `gunicorn config.wsgi --bind 0.0.0.0:8000
--workers 2`). `gunicorn` entra no `requirements.txt` (é dependência de execução).

---

## R-03 — Interface: build do Vite servido por Nginx sem root

**Decisão**: o `frontend/Dockerfile` ganha estágios `dev` (o atual), `build` (`npm ci` +
`npm run build`) e `uso` (`nginxinc/nginx-unprivileged:1.28-alpine`, porta 8080, sem root) com
`frontend/nginx.conf`:

- arquivos de `dist/`; rotas da interface caem no `index.html` (`try_files`);
- `/api/` → `http://backend:8000`, com `Host: backend` fixo e `X-Forwarded-For` (o limite de
  login continua por dispositivo, FR-008; `GRANA_PROXY_CONFIAVEL=frontend` não muda);
- `server_tokens off` (sem versão nos cabeçalhos e páginas de erro);
- cache longo para `/assets/` (nomes com hash) e `no-cache` para o `index.html`;
- cabeçalhos `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin` e
  `X-Frame-Options: DENY`.

Porta publicada: `${FRONTEND_PORT:-5173}:8080` (mesmo endereço do modo de desenvolvimento).

---

## R-04 — Hosts fixos e API só pela interface

**Decisão**: no modo de uso, `DJANGO_ALLOWED_HOSTS=backend,localhost` fixo (o Nginx sempre envia
`Host: backend`; `localhost` é o healthcheck). O `Host` que vem do navegador nunca chega ao
Django, então não há *Host header poisoning* e o acesso pelo IP da máquina continua funcionando.
A porta 8000 não é publicada.

---

## R-05 — Depuração desligada e chave obrigatória

**Decisão**: `DJANGO_DEBUG=0` fixo no modo de uso. `DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:?...}`
faz o próprio Compose recusar a subida, antes de construir, com a mensagem "Defina
DJANGO_SECRET_KEY no .env (veja o README) para usar o modo de uso."; a validação das settings
(spec 001, FR-012) continua como segunda barreira. O README traz o comando para gerar uma chave.

---

## R-06 — Avisos do `check --deploy`

**Decisão**: rodar `python manage.py check --deploy` na imagem de uso e:

- silenciar, só fora da depuração, os avisos de HTTPS que não se aplicam à rede doméstica sem
  certificado: `security.W004` (HSTS), `security.W008` (redirecionar para HTTPS),
  `security.W012` e `security.W016` (cookies seguros; o sistema não usa cookies de sessão nem
  CSRF, a sessão é por token);
- tratar qualquer outro aviso que aparecer.

---

## R-07 — Validação

**Decisão**: infraestrutura é validada pelo quickstart (constituição, Princípio IV): subir o modo
de uso, conferir build otimizado, servidor de aplicação, erros genéricos, cabeçalhos, porta 8000
fechada, recusa sem chave, usuário dos processos e troca de modo com contagem de dados. As suítes
continuam no modo de desenvolvimento.
