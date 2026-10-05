# Contrato: Isolamento nos endpoints de dados

**Feature**: `004-isolamento-usuario` | **Requisitos**: FR-002 a FR-008, FR-011

Este contrato não cria rotas na aplicação. Ele define o comportamento que **todo endpoint de
dados financeiros** (a partir da US-05) MUST seguir, e que os contratos das próximas specs
referenciam em vez de repetir. Nos exemplos, `/api/<recurso>/` representa qualquer recurso de
dados (categorias, meses, gastos, cenários).

## Pré-condição: sessão

Todo endpoint de dados exige credencial de acesso válida (spec 003,
[api-sessao.md](../../003-login-logout/contracts/api-sessao.md)). Sem ela, a resposta é 401 e
nenhum dado é consultado.

## Regras

### 1. Listas, buscas, filtros e totais (FR-004, FR-008)

`GET /api/<recurso>/` (com ou sem parâmetros de busca e filtro) devolve **apenas** registros do
usuário da sessão. Totais e contagens também.

| Situação | Resposta |
|---|---|
| Usuário com registros | 200, só os dele |
| Usuário sem registros (mesmo que outras contas tenham) | 200, `[]` |

### 2. Registro por identificador (FR-005)

`GET`, `PUT`, `PATCH` e `DELETE` em `/api/<recurso>/<id>/`:

| Situação | Resposta |
|---|---|
| Registro do próprio usuário | resposta normal do recurso (200 / 204) |
| Registro de outra conta | **404** `{"detail": "Não encontrado."}` e nada é alterado |
| Identificador inexistente | **404** `{"detail": "Não encontrado."}` |
| Identificador mal formado (ex.: `abc`) | **404** `{"detail": "Não encontrado."}` |

As três respostas 404 MUST ser idênticas (código e corpo). Nunca se usa 403 para registro de outra
conta.

### 3. Dono (FR-002, FR-003)

- O campo `dono` **não existe** na API: não aparece nas respostas e é **ignorado** se vier no
  payload de criação ou de alteração. Não é um erro enviá-lo.
- O dono é sempre o usuário da sessão.

```http
POST /api/<recurso>/
{"nome": "Mercado", "dono": 2}
```

→ 201, e o registro pertence ao usuário da sessão, seja qual for o valor de `dono`.

### 4. Referências a outros registros (FR-006)

Campos que apontam para outro registro de dados (ex.: `"categoria": 7` num gasto) só aceitam
registros do próprio usuário. Referência a registro de outra conta ou inexistente:

```json
HTTP 400
{"categoria": ["Registro não encontrado."]}
```

A mensagem é a mesma nos dois casos.

### 5. Unicidade (FR-007)

Regras de "único" valem dentro da conta. Duas contas podem ter registros com o mesmo nome. Um
nome repetido **na mesma conta** produz 400 no formato de validação do DRF, com mensagem em
pt-BR que não cita o campo `dono` (texto exato definido por cada recurso; [R-05](../research.md)).

## Testes obrigatórios por recurso (FR-011)

Todo endpoint de dados MUST ter uma subclasse do kit `tests/isolamento.py`
(`CasosDeIsolamento`, [R-08](../research.md)), que cobre:

1. a lista mostra só os registros do dono;
2. a lista vem vazia, sem erro, para quem não tem registros;
3. abrir registro de outra conta → 404 idêntico ao de id inexistente;
4. alterar registro de outra conta → 404, registro intacto;
5. excluir registro de outra conta → 404, registro continua existindo;
6. `dono` no payload de criação é ignorado;
7. `dono` no payload de alteração é ignorado.

Recursos com referências ou unicidade acrescentam os testes das regras 4 e 5.
