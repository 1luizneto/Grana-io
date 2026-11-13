# Contrato: Modos de Execução

**Feature**: `011-modo-de-uso` | **Requisitos**: FR-001 a FR-009

## Comandos

| Modo | Comando | Endereço |
|---|---|---|
| Desenvolvimento | `docker compose up -d --build --wait` | interface `:5173`, API `:8000` |
| Uso | `docker compose -f compose.yaml -f compose.uso.yaml up -d --build --wait` | interface `:5173` (API só por `/api`) |
| Parar (qualquer um) | `docker compose down` | — |

Trocar de modo = rodar o comando do outro. Os dados ficam no mesmo volume (`grana_pgdata`).

## Diferenças

| Aspecto | Desenvolvimento | Uso |
|---|---|---|
| Interface | servidor do Vite, recarga automática | build otimizado servido pelo Nginx |
| API | `runserver`, recarga automática | Gunicorn, 2 processos |
| Código | montado do computador | dentro da imagem |
| `DJANGO_DEBUG` | `1` (padrão) | `0` (fixo) |
| `DJANGO_SECRET_KEY` | opcional (chave padrão) | **obrigatória** no `.env` |
| `DJANGO_ALLOWED_HOSTS` | `*` (padrão) | `backend,localhost` (fixo) |
| Porta da API no computador | `${BACKEND_PORT:-8000}` | não publicada |
| Usuário nos containers | padrão da imagem | sem privilégios (`grana` e `nginx`) |
| Versão do servidor nas respostas | — | omitida |

## Recusa sem chave

Sem `DJANGO_SECRET_KEY` no `.env`, o comando do modo de uso para antes de subir, com a mensagem:
"Defina DJANGO_SECRET_KEY no .env (veja o README) para usar o modo de uso.".

Gerar uma chave:

```bash
docker compose run --rm backend python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

## Variáveis que continuam valendo no modo de uso

`POSTGRES_*`, `GRANA_CADASTRO_ABERTO`, `GRANA_SESSAO_*`, `GRANA_LOGIN_TENTATIVAS_POR_MINUTO`,
`FRONTEND_PORT`. `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `BACKEND_PORT` e `VITE_API_URL` são
ignoradas (fixas no modo de uso).
