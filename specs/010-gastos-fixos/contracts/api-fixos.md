# Contrato: API de Gastos Fixos

**Feature**: `010-gastos-fixos` | **Requisitos**: FR-001 a FR-008, FR-010

Rotas com sessão (spec 003) e isolamento (spec 004): fixo de outra conta, inexistente ou id mal
formado → `404 {"detail": "Não encontrado."}`.

## Representação

```json
{ "id": 3, "descricao": "Aluguel", "valor": "1500.00", "categoria": 2, "forma_pagamento": "pix",
  "dia_vencimento": 5, "inicio": "2026-11", "fim": null, "ativo": true }
```

## `GET /api/fixos/`

**200**: fixos da pessoa por dia de vencimento e cadastro.

## `POST /api/fixos/` · `PATCH`/`PUT /api/fixos/{id}/` · `GET`/`DELETE /api/fixos/{id}/`

Campos obrigatórios na criação: `descricao`, `valor`, `categoria`, `dia_vencimento`, `inicio`.
Opcionais: `forma_pagamento`, `fim` (`null` = sem fim), `ativo` (padrão `true`).

| Situação | Resposta 400 |
|---|---|
| descrição, valor, categoria, forma | mesmas mensagens dos gastos ([spec 008](../../008-lancar-gastos/contracts/api-gastos.md)) |
| dia fora de 1 a 31 ou não inteiro | `{"dia_vencimento": ["Informe um dia de 1 a 31."]}` |
| mês fora do formato `AAAA-MM` | `{"inicio": ["Informe o mês no formato AAAA-MM."]}` (idem `fim`) |
| ano fora de 2000 a 2100 | `{"inicio": ["Informe um ano de 2000 a 2100."]}` (idem `fim`) |
| fim antes do início | `{"fim": ["O mês de fim precisa ser igual ou posterior ao de início."]}` |

`DELETE` → 204; os gastos gerados continuam (com `"fixo": null`). Nada disso altera meses
existentes.

## Mudanças em rotas existentes

- **Gasto** (spec 008): a representação ganha `"fixo": <id> | null` (só leitura).
  `POST /api/gastos/` aceita `"repetir": true`: lança o gasto e cria o fixo (vencimento = dia da
  data; início = mês do gasto), tudo ou nada; a resposta traz `"fixo": <id do fixo novo>`.
- **Mês** (spec 007): `POST /api/meses/` também gera os gastos dos fixos ativos do período, na
  mesma transação.
- **Categoria** (spec 008): `DELETE /api/categorias/{id}/` trata fixos como gastos: com fixos e
  sem `mover_para` → a mesma recusa; com destino, os fixos também passam para ele.
