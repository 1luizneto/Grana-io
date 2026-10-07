# Contrato: API de Categorias

**Feature**: `006-categorias-gasto` | **Requisitos**: FR-001 a FR-010

Todas as rotas exigem sessão (spec 003) e seguem o
[contrato de isolamento](../../004-isolamento-usuario/contracts/isolamento.md): só as categorias
de quem está conectado aparecem e podem ser alteradas; categoria de outra conta, id inexistente e
id mal formado respondem `404 {"detail": "Não encontrado."}`. O campo `dono` não existe na API.

## `GET /api/categorias/`

**200 OK**: as categorias da pessoa, em ordem alfabética sem diferenciar maiúsculas.

```json
[
  { "id": 3, "nome": "Alimentação", "cor": "laranja" },
  { "id": 6, "nome": "Educação", "cor": "ciano" }
]
```

Lista vazia: `[]`.

## `POST /api/categorias/`

**Requisição**: `{ "nome": "Pets", "cor": "verde" }`. `cor` é opcional.

**201 Created**: `{ "id": 15, "nome": "Pets", "cor": "verde" }`. Sem `cor`, a resposta traz a cor
atribuída automaticamente (a primeira da paleta ainda não usada pela pessoa).

**400 Bad Request** (todas as mensagens de uma vez, por campo):

| Situação | Resposta |
|---|---|
| Nome vazio ou só espaços | `{"nome": ["Este campo é obrigatório."]}` |
| Nome com mais de 50 caracteres | `{"nome": ["Certifique-se de que este campo não tenha mais de 50 caracteres."]}` |
| Nome já usado na conta (sem diferenciar maiúsculas) | `{"nome": ["Já existe uma categoria com este nome."]}` |
| Cor fora da paleta | `{"cor": ["Escolha uma das cores disponíveis."]}` |

O texto exato do limite de tamanho é o do DRF em pt-BR; a implementação confirma.

## `GET /api/categorias/{id}/`

**200 OK**: `{ "id": 15, "nome": "Pets", "cor": "verde" }`.

## `PATCH /api/categorias/{id}/` e `PUT /api/categorias/{id}/`

Renomear e/ou trocar a cor (`PATCH` aceita só um dos campos). Mesmas regras e erros do `POST`.
Renomear para o próprio nome, mudando só maiúsculas, é aceito.

**200 OK**: a categoria atualizada.

## `DELETE /api/categorias/{id}/`

**204 No Content**. A exclusão é livre nesta spec; a US-07 acrescenta a escolha da categoria de
destino quando houver gastos vinculados (Clarifications Q2).

## `GET /api/categorias/cores/`

**200 OK**: a paleta, na ordem em que deve ser exibida.

```json
[
  { "codigo": "azul", "nome": "Azul", "hex": "#2563EB" },
  { "codigo": "laranja", "nome": "Laranja", "hex": "#EA580C" }
]
```

(12 itens; lista completa em [research R-02](../research.md)).

## Categorias padrão

Criadas no cadastro (`POST /api/usuarios/`, spec 002) e, uma única vez, para contas antigas sem
categorias: Moradia (azul), Alimentação (laranja), Transporte (roxo), Saúde (vermelho), Lazer
(rosa), Educação (ciano), Outros (cinza). A resposta do cadastro não muda.
