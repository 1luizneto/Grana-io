# Data Model: Categorias de Gasto

**Feature**: `006-categorias-gasto` | **Plano**: [plan.md](plan.md)

## `Categoria(OwnedModel)` — app `gastos`

| Campo | Tipo | Regras |
|---|---|---|
| `id` | inteiro sequencial | Spec 004 (Clarifications). |
| `dono` | FK → `accounts.Usuario` (herdado) | Definido pela sessão; nunca muda; exclusão em cascata com a conta (spec 004). |
| `nome` | `CharField(max_length=50)` | Obrigatório; sem espaços nas pontas; de 1 a 50 caracteres. Único por dono **sem diferenciar maiúsculas** (FR-005). |
| `cor` | `CharField(max_length=20, choices=PALETA)` | Código de uma das 12 cores ([research R-02](research.md)). Obrigatório no banco; a API atribui uma automaticamente se não vier (R-07). |

**Constraint**: `UniqueConstraint(Lower("nome"), "dono", name="gastos_categoria_nome_por_dono",
violation_error_message="Já existe uma categoria com este nome.")`.

**Ordenação padrão**: `Lower("nome")` (FR-003).

**Relações futuras**: o `Gasto` (US-07) terá FK para `Categoria`; a regra de exclusão com destino
entra lá (Clarifications Q2).

## Paleta (`gastos/cores.py`, código, sem tabela)

Tupla ordenada de 12 `Cor(codigo, nome, hex)`, conforme [research R-02](research.md). É a fonte
única: o `choices` do campo `cor`, a validação da API e a resposta de `/api/categorias/cores/`
saem dela.

## Categorias padrão (`gastos/services/categorias.py`, código)

7 pares `(nome, cor)`, conforme [research R-03](research.md). Criadas:

- no cadastro, na mesma transação da conta ([R-04](research.md));
- uma única vez para contas antigas sem categorias, pela migration de dados ([R-05](research.md)).

## Estados

Não há estados. Criar → renomear/trocar cor → excluir, sempre restrito ao dono.
