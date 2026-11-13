# Data Model: Lançar, Editar e Excluir Gastos

**Feature**: `008-lancar-gastos` | **Plano**: [plan.md](plan.md)

## `Gasto(OwnedModel)` — app `gastos`

| Campo | Tipo | Regras |
|---|---|---|
| `id` | inteiro sequencial | Spec 004. |
| `dono` | FK → `accounts.Usuario` (herdado) | Pela sessão; cascata com a conta. |
| `descricao` | `CharField(max_length=100)` | Obrigatória; espaços das pontas removidos. |
| `valor` | `DecimalField(max_digits=12, decimal_places=2)` | `> 0` (`CheckConstraint` `gastos_gasto_valor_positivo`); até 9999999999.99. |
| `data` | `DateField` | Dentro do mês de referência (validado na API). |
| `forma_pagamento` | `CharField(max_length=10, choices=FORMAS_PAGAMENTO, blank=True, default="")` | `dinheiro`, `debito`, `credito`, `pix` ou vazio. |
| `mes` | FK → `MesReferencia`, `on_delete=RESTRICT`, `related_name="gastos"` | Da mesma pessoa; aberto para criar, alterar e excluir. |
| `categoria` | FK → `Categoria`, `on_delete=RESTRICT`, `related_name="gastos"` | Da mesma pessoa. |

**Ordenação padrão**: `["data", "id"]`.

## Efeitos nas entidades existentes

- **MesReferencia** (spec 007): com gastos, não se exclui (FR-009; `RESTRICT` no banco e mensagem
  na API). Fechado, bloqueia criar, alterar, mover e excluir gastos (FR-008).
- **Categoria** (spec 006): com gastos, só se exclui com destino; os gastos passam para o destino
  antes (FR-010; `RESTRICT` no banco).
- **Usuario**: excluir a conta apaga categorias, meses e gastos em cascata (o `RESTRICT` libera
  porque os gastos também são apagados).

## Derivados (não gravados)

- **Totais do mês**: soma dos `valor` do mês e por categoria, `Decimal` com 2 casas
  (`ROUND_HALF_UP`, `core/dinheiro.py`).
