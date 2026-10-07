# Contrato: API de Meses de Referência

**Feature**: `007-mes-referencia` | **Requisitos**: FR-001 a FR-010

Todas as rotas exigem sessão (spec 003) e seguem o
[contrato de isolamento](../../004-isolamento-usuario/contracts/isolamento.md): mês de outra conta,
id inexistente e id mal formado respondem `404 {"detail": "Não encontrado."}`. O campo `dono` não
existe na API.

## Representação

```json
{ "id": 7, "mes": 10, "ano": 2026, "rotulo": "10/2026", "fechado": false }
```

`rotulo` é somente leitura.

## `GET /api/meses/`

**200 OK**: os meses da pessoa em ordem cronológica crescente (ano, depois mês). Sem meses: `[]`.

## `POST /api/meses/`

**Requisição**: `{ "mes": 10, "ano": 2026 }` (aceita `"10"` e `"2026"` como texto).

**201 Created**: o mês criado, com `"fechado": false`. Todo mês nasce aberto: `fechado` enviado na
criação é ignorado.

**400 Bad Request** (todas as mensagens de uma vez, por campo):

| Situação | Resposta |
|---|---|
| Mês ou ano ausente/vazio | `{"mes": ["Este campo é obrigatório."]}` (idem `ano`) |
| Mês fora de 1 a 12 ou não inteiro | `{"mes": ["Informe um mês de 1 a 12."]}` |
| Ano fora de 2000 a 2100 ou não inteiro | `{"ano": ["Informe um ano de 2000 a 2100."]}` |
| Mês e ano já criados na conta | `{"non_field_errors": ["Este mês já foi criado."]}` |

## `GET /api/meses/{id}/`

**200 OK**: o mês.

## `PATCH /api/meses/{id}/` (fechar e reabrir)

**Requisição**: `{ "fechado": true }` (fechar) ou `{ "fechado": false }` (reabrir).

**200 OK**: o mês atualizado. Repetir o mesmo estado é aceito.

**400 Bad Request**: tentar trocar `mes` ou `ano` por outro valor →
`{"mes": ["Não é possível alterar o mês ou o ano. Exclua o mês e crie de novo."]}` (ou no campo
`ano`). Enviar o mesmo valor atual é aceito (ex.: `PUT` com o objeto inteiro).

## `DELETE /api/meses/{id}/`

**204 No Content**: mês aberto excluído.

**400 Bad Request**: mês fechado → `{"detail": "Reabra o mês antes de excluí-lo."}`; nada muda.

A partir da US-07, um mês com gastos também é recusado:
`{"detail": "Exclua ou mova os gastos antes de excluir o mês."}` (Clarifications).
