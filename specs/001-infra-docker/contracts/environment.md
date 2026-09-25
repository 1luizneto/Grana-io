# Contrato: Variáveis de ambiente

**Feature**: `001-infra-docker` | **Requisitos**: FR-009, FR-010, FR-011, FR-012, FR-013

Este é o contrato das variáveis lidas do `.env` da raiz (opcional, nunca versionado). O
`.env.example` versionado MUST listar todas as variáveis da tabela "Configuráveis", com o mesmo
padrão e um comentário explicativo.

## Configuráveis pelo `.env`

| Variável | Consumidor | Padrão de desenvolvimento | Descrição |
|---|---|---|---|
| `POSTGRES_DB` | db, backend | `grana` | Nome do banco principal. |
| `POSTGRES_USER` | db, backend | `grana` | Usuário do banco. |
| `POSTGRES_PASSWORD` | db, backend | `grana-dev-senha` | Senha do banco. Só vale ao inicializar um volume vazio. |
| `DJANGO_SECRET_KEY` | backend | *(vazia → chave padrão de dev definida em `config/env.py`)* | Chave secreta do Django. Obrigatória fora do modo de desenvolvimento (FR-012). |
| `DJANGO_DEBUG` | backend | `1` | Modo de desenvolvimento (`1`/`0`). |
| `DJANGO_ALLOWED_HOSTS` | backend | `*` | Hosts aceitos, separados por vírgula. `*` só no modo de desenvolvimento ([research R-07](../research.md)). Um valor personalizado MUST incluir `localhost` (healthcheck do container) e `backend` (proxy do Vite, que envia `Host: backend:8000`), além do IP da máquina. Ex.: `localhost,backend,192.168.0.10`. |
| `DJANGO_CORS_ALLOWED_ORIGINS` | backend | *(vazia)* | Origens extras autorizadas a chamar a API pelo navegador, separadas por vírgula (ex.: `http://localhost:3000`). A própria interface não precisa estar aqui ([research R-06](../research.md)). |
| `BACKEND_PORT` | compose | `8000` | Porta do host para a API. |
| `FRONTEND_PORT` | compose | `5173` | Porta do host para a interface. |
| `VITE_API_URL` | frontend | *(vazia → `/api`, no mesmo endereço da interface, via proxy)* | URL base absoluta da API, **incluindo** o `/api` (ex.: `http://localhost:8000/api`), para cenários futuros (RNF-08). |

## Fixas no `compose.yaml` (internas, fora do `.env.example`)

| Variável | Consumidor | Valor | Motivo |
|---|---|---|---|
| `POSTGRES_HOST` | backend | `db` | Nome do serviço na rede interna. |
| `POSTGRES_PORT` | backend | `5432` | Porta interna do PostgreSQL. |
| `API_PROXY_TARGET` | frontend (vite.config) | `http://backend:8000` | Destino do proxy `/api`, na rede interna. Não tem prefixo `VITE_`, portanto não vai para o navegador. |

## Regras

1. Sem `.env`, o sistema sobe com os padrões acima (FR-010).
2. Com `.env`, os valores dele prevalecem sobre os padrões (FR-010).
3. `.env` está no `.gitignore` e `.env.example` é versionado (FR-011).
4. `DJANGO_DEBUG=0` com `DJANGO_SECRET_KEY` vazia ou igual à chave padrão impede o início da API,
   com mensagem citando `DJANGO_SECRET_KEY` (FR-012).
5. Os valores de exemplo são claramente de desenvolvimento (contêm `dev`/`insecure`). Nenhum valor
   real é versionado (SC-004).
6. Só variáveis com prefixo `VITE_` chegam ao código do navegador. Segredos nunca usam esse prefixo.
