# Implementation Plan: Modo de Uso

**Branch**: `011-modo-de-uso` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Backlog**: RNF-09 (Sprint 2), com as pendências da spec 001.

## Summary

Arquivo de sobreposição `compose.uso.yaml` que troca os serviços para imagens de uso: API com
Gunicorn e interface com o build do Vite servido por Nginx, ambos sem root, sem código montado,
depuração desligada, chave obrigatória, hosts fixos e só a interface exposta. Mesmo projeto e
mesmo volume do modo de desenvolvimento. Detalhes em [research.md](research.md).

## Technical Context

**Language/Version**: Dockerfile, Compose, Nginx; Python 3.12 (settings).

**Primary Dependencies**: novas: `gunicorn==23.0.0` (Python) e a imagem
`nginxinc/nginx-unprivileged:1.28-alpine`.

**Storage**: o mesmo volume `grana_pgdata`.

**Testing**: suítes atuais (modo de desenvolvimento) + validação do quickstart.

**Project Type**: infraestrutura da aplicação web.

**Constraints**: um comando por modo; nenhum dado perdido; nenhum detalhe técnico na rede.

## Constitution Check

| # | Princípio / regra | Avaliação | Pós-design |
|---|---|---|---|
| I | Localidade e privacidade | Tudo local; menos superfície na rede. | ✅ API sem porta publicada; sem versões nos cabeçalhos; segredo obrigatório e fora do Git (`.env`). |
| II | Isolamento | Sem mudança. | ✅ |
| III | Precisão monetária | Sem mudança. | ✅ |
| IV | Testes | Infra é validada pelo quickstart. | ✅ S1 a S6; suítes continuam verdes. |
| V | Separação | A interface chama `/api` como antes. | ✅ |
| VI | Simplicidade | Sobreposição do Compose, sem orquestrador nem scripts extras. | ✅ |
| — | Dependências novas | Justificadas: servidor de aplicação e servidor web são o próprio critério do RNF-09. | ✅ |
| — | Workflow | Branch empilhada sobre a 010 (modo autônomo). | ✅ |

## Project Structure

```text
compose.yaml                   # alvo "dev" explícito nos builds
compose.uso.yaml               # novo: sobreposição do modo de uso
backend/Dockerfile             # estágios dev e uso
backend/requirements.txt       # + gunicorn
backend/scripts/start-uso.sh   # migrate + gunicorn
backend/config/settings.py     # avisos de HTTPS silenciados fora da depuração
frontend/Dockerfile            # estágios dev, build e uso
frontend/nginx.conf            # novo
frontend/.dockerignore         # conferir node_modules e dist
.env.example, README.md
```

## Complexity Tracking

Nenhuma violação.

## Pontos de atenção

1. **`!reset` do Compose** (volumes e portas) exige Compose 2.24+; o Docker Desktop atual traz
   bem mais. Conferir com `docker compose version`.
2. **Imagem de testes**: `docker compose run --rm backend pytest` continua usando o alvo `dev`.
3. **Ambiente do responsável**: ao fim da validação, voltar ao modo de desenvolvimento.
