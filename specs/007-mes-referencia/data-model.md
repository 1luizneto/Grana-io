# Data Model: Mês de Referência

**Feature**: `007-mes-referencia` | **Plano**: [plan.md](plan.md)

## `MesReferencia(OwnedModel)` — app `gastos`

| Campo | Tipo | Regras |
|---|---|---|
| `id` | inteiro sequencial | Spec 004. |
| `dono` | FK → `accounts.Usuario` (herdado) | Pela sessão; nunca muda; cascata com a conta (spec 004). |
| `mes` | `PositiveSmallIntegerField` | 1 a 12 (`CheckConstraint` `gastos_mes_mes_valido`). Só na criação (FR-006). |
| `ano` | `PositiveSmallIntegerField` | 2000 a 2100 (`CheckConstraint` `gastos_mes_ano_valido`). Só na criação (FR-006). |
| `fechado` | `BooleanField(default=False)` | Nasce aberto; alterável pelo dono a qualquer momento (FR-004). |

**Constraint de unicidade**: `UniqueConstraint(fields=["dono", "ano", "mes"],
name="gastos_mes_unico_por_dono", violation_error_message="Este mês já foi criado.")` (FR-002).

**Ordenação padrão**: `["ano", "mes"]` (FR-003).

**Derivado na API**: `rotulo = f"{mes:02d}/{ano}"` (ex.: `"03/2027"`), somente leitura.

## Estados

```text
           criar
  ──────────────────▶  aberto  ◀──── reabrir ────┐
                         │                       │
                         └────── fechar ──────▶ fechado
  excluir: só aberto (FR-005); com gastos, bloqueado a partir da US-07 (FR-010)
```

Fechar o que já está fechado, ou reabrir o que já está aberto, é aceito e não muda nada.

## Relações futuras

O `Gasto` (US-07) terá FK para `MesReferencia`; a US-07 e a US-08 consultam `fechado` para
bloquear lançar, editar e excluir gastos (FR-007), e a US-07 acrescenta o bloqueio de excluir mês
com gastos (FR-010).
