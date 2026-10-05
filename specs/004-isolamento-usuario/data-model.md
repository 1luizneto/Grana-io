# Data Model: Isolamento de Dados por Usuário

**Feature**: `004-isolamento-usuario` | **Plano**: [plan.md](plan.md)

Esta spec não cria tabelas no banco de uso. Ela define uma **base abstrata** que os próximos
models herdam, e dois models de exemplo que existem só no banco de testes.

## `OwnedModel` (abstrato, `core/models.py`)

Base de todo registro de dados financeiros (FR-001, FR-009).

| Campo | Tipo | Regras |
|---|---|---|
| `dono` | FK → `accounts.Usuario` | Obrigatório. `on_delete=CASCADE` (FR-012). `editable=False`. `related_name="+"`. Definido pelo servidor a partir da sessão (FR-002) e nunca alterado (FR-003). Indexado (FK). |

**Manager**: `objects = RegistroDoDonoQuerySet.as_manager()`

| Método | Retorno | Uso |
|---|---|---|
| `do_dono(usuario)` | queryset filtrado por `dono=usuario` | Ponto único do filtro, usado pelo mixin da API (R-02), pelo campo de referência (R-04) e pelos services (totais, FR-004). |

**Convenções para quem herda**:
- unicidade de nome: `UniqueConstraint(fields=["dono", "nome"], name="<app>_<model>_nome_por_dono")`,
  nunca `unique=True` sozinho (FR-007; [R-05](research.md));
- FK para outro registro com dono: o serializer usa `RelacionadoDoDonoField` (FR-006;
  [R-04](research.md));
- valores monetários: `DecimalField` (constituição, Princípio III).

**Relação**: `Usuario` 1 — 0..N registro com dono. Sem acesso reverso pelo usuário (`related_name="+"`).

## `Usuario` (spec 002)

Sem alteração de campos. Fica na lista de exceções da guarda (`MODELS_SEM_DONO`), por ser o
próprio dono e não um registro com dono.

## Exceções: dados de referência compartilhados

Pela constituição (v1.2.0, Princípio II), só ficam sem dono os dados que não pertencem a ninguém,
valem para todos e são somente leitura pela API (ex.: faixas de INSS e IRRF por ano, US-15).
Cada um entra em `MODELS_SEM_DONO`, com comentário citando a spec, e é justificado no `plan.md`
dela. Nesta spec, a única exceção é o `Usuario`.

## Models de exemplo (só no banco de testes, app `tests.exemplo`)

Existem para provar o isolamento antes da US-05 (FR-013; [R-07](research.md)). Não têm migration,
não estão no `INSTALLED_APPS` de uso e não têm rotas na aplicação.

### `GrupoExemplo(OwnedModel)`

| Campo | Tipo | Regras |
|---|---|---|
| `nome` | `CharField(60)` | Obrigatório. Único **por dono**: `UniqueConstraint(dono, nome)` (FR-007). |

### `ItemExemplo(OwnedModel)`

| Campo | Tipo | Regras |
|---|---|---|
| `descricao` | `CharField(100)` | Obrigatório. Pesquisável por `?busca=` (FR-004). |
| `valor` | `DecimalField(12, 2)` | Obrigatório. Somado na ação `total` (FR-004). |
| `grupo` | FK → `GrupoExemplo`, opcional | `on_delete=SET_NULL`. Só aceita grupo do mesmo dono (FR-006). |

Ordenação padrão por `id`.

## Estados e transições

Não há estados. O ciclo de vida é criar → alterar → excluir, sempre restrito ao dono. O dono não
muda em nenhuma transição.
