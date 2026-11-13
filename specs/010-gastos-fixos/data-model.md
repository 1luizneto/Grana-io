# Data Model: Gastos Fixos

**Feature**: `010-gastos-fixos` | **Plano**: [plan.md](plan.md)

## `GastoFixo(OwnedModel)` — app `gastos`

| Campo | Tipo | Regras |
|---|---|---|
| `descricao` | `CharField(max_length=100)` | Obrigatória. |
| `valor` | `DecimalField(max_digits=12, decimal_places=2)` | `> 0` (`gastos_fixo_valor_positivo`). |
| `forma_pagamento` | `CharField(max_length=10, choices=FORMAS_PAGAMENTO, blank=True, default="")` | Como no gasto. |
| `categoria` | FK → `Categoria`, `RESTRICT`, `related_name="fixos"` | Da mesma pessoa. |
| `dia_vencimento` | `PositiveSmallIntegerField` | 1 a 31 (`gastos_fixo_dia_valido`). |
| `inicio` | `DateField` | Dia 1 do mês de início. |
| `fim` | `DateField(null=True, blank=True)` | Dia 1 do mês de fim; `>= inicio` (`gastos_fixo_fim_depois_do_inicio`). |
| `ativo` | `BooleanField(default=True)` | Desativado não gera. |

**Ordenação**: `["dia_vencimento", "id"]`.

## `Gasto` (spec 008) — campo novo

| Campo | Tipo | Regras |
|---|---|---|
| `fixo` | FK → `GastoFixo`, `null=True`, `blank=True`, `SET_NULL`, `related_name="gastos_gerados"` | Origem do gasto gerado; só leitura na API. |

## Geração (derivado, ao criar um mês)

Para o mês M (dia 1 = `d`): fixos com `ativo`, `inicio <= d` e (`fim` nulo ou `fim >= d`) →
um gasto cada, data = dia `min(dia_vencimento, último dia de M)`.
