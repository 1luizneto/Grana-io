# Data Model: Execução Local com Um Comando (Infraestrutura Docker)

**Feature**: `001-infra-docker` | **Data**: 2026-09-25 | **Plano**: [plan.md](plan.md)

Esta feature **não cria entidades de domínio nem tabelas próprias**. As primeiras entidades de
domínio (usuário, `OwnedModel`) chegam nas specs 002 e 003. As únicas tabelas criadas são as dos
apps nativos do Django instalados nesta spec (`auth` e `contenttypes`), pela migração automática
do FR-004. O `admin` entra quando algum item do backlog precisar dele (ex.: US-04).

Abaixo estão os três elementos da seção *Key Entities* da spec, descritos como estruturas técnicas.

---

## 1. Dados persistidos (volume do banco)

| Atributo | Valor |
|---|---|
| Recurso | Volume Docker nomeado `pgdata`, resolvido como `grana_pgdata` (projeto `name: grana`) |
| Montado em | `db:/var/lib/postgresql/data` |
| Banco principal | `${POSTGRES_DB}` (padrão `grana`) |
| Banco de testes | `test_${POSTGRES_DB}` (padrão `test_grana`), criado e removido a cada execução do pytest |
| Acesso | Só pela rede interna do Compose (`db:5432`); sem porta publicada (FR-019) |

**Ciclo de vida**

```text
(inexistente) --1ª subida--> inicializado (vazio + migrations)
inicializado  --up/down/restart/build/reboot--> inicializado (dados preservados)   [FR-005]
inicializado  --docker compose down -v--> (inexistente)                          [FR-006]
```

**Regras**
- Só `docker compose down -v` (ou `docker volume rm grana_pgdata`) remove os dados.
- `POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB` só têm efeito na inicialização de um volume
  vazio (ver [research.md R-05](research.md#r-05--persistência-e-remoção-dos-dados-fr-005-fr-006-fr-019)).

## 2. Configuração de ambiente

É o conjunto de variáveis de ambiente descrito em
[contracts/environment.md](contracts/environment.md), que é a fonte da verdade sobre nomes,
padrões e consumidores.

**Regras de validação**
- Variável ausente no `.env` recebe o padrão de desenvolvimento do `compose.yaml` (FR-010).
- `DJANGO_DEBUG` é interpretada como booleano (`1/true/yes/on` → verdadeiro; qualquer outro
  valor → falso). O padrão no `settings.py`, fora do compose, é **falso**.
- `DJANGO_ALLOWED_HOSTS` e `DJANGO_CORS_ALLOWED_ORIGINS` são listas separadas por vírgula, e
  itens vazios são ignorados.
- Se `DJANGO_DEBUG` for falso e `DJANGO_SECRET_KEY` estiver vazia ou igual à chave padrão de
  desenvolvimento, a API **não inicia** e a mensagem cita `DJANGO_SECRET_KEY` (FR-012).

## 3. Verificação de saúde

É uma resposta sem persistência. O contrato completo está em
[contracts/api-health.md](contracts/api-health.md).

| Campo | Tipo | Valores |
|---|---|---|
| `status` | string | `ok` \| `error` |
| `database` | string | `ok` \| `unavailable` |

**Estados**

| Banco acessível? | HTTP | `status` | `database` |
|---|---|---|---|
| Sim | 200 | `ok` | `ok` |
| Não | 503 | `error` | `unavailable` |

A resposta nunca inclui mensagens de exceção, hosts, portas, nomes de banco ou credenciais.
