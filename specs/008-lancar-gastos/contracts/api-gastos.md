# Contrato: API de Gastos

**Feature**: `008-lancar-gastos` | **Requisitos**: FR-001 a FR-013

Todas as rotas exigem sessão (spec 003) e seguem o
[contrato de isolamento](../../004-isolamento-usuario/contracts/isolamento.md): gasto de outra
conta, id inexistente e id mal formado respondem `404 {"detail": "Não encontrado."}`. O campo
`dono` não existe na API.

## Representação

```json
{ "id": 41, "descricao": "Mercado", "valor": "150.30", "data": "2026-10-05",
  "forma_pagamento": "pix", "mes": 7, "categoria": 3 }
```

`valor` sai como texto com 2 casas. `forma_pagamento` vazio é `""`.

## `GET /api/gastos/`

**200 OK**: gastos da pessoa por data e, na mesma data, por lançamento.

- `?mes=<id>`: só os do mês; `?categoria=<id>`: só os da categoria (combináveis).
- Id de outra conta → `[]`. Id que não é número → `400 {"mes": ["Informe o número do mês."]}`
  (ou `{"categoria": ["Informe o número da categoria."]}`).

## `POST /api/gastos/`

**Requisição**: `{"descricao", "valor", "data", "mes", "categoria", "forma_pagamento"?}`.

**201 Created**: o gasto criado.

**400 Bad Request** (erros de campo de uma vez):

| Situação | Resposta |
|---|---|
| campo obrigatório ausente, vazio ou nulo | `{"<campo>": ["Este campo é obrigatório."]}` |
| descrição com mais de 100 caracteres | `{"descricao": ["Certifique-se de que este campo não tenha mais de 100 caracteres."]}` |
| valor não numérico | `{"valor": ["Informe um valor numérico, como 12.50."]}` |
| valor zero ou negativo | `{"valor": ["Informe um valor maior que zero."]}` |
| valor com mais de 2 casas | `{"valor": ["Use no máximo 2 casas decimais."]}` |
| valor acima do limite | `{"valor": ["Informe um valor de até 9999999999.99."]}` |
| data inválida | `{"data": ["Informe uma data válida no formato AAAA-MM-DD."]}` |
| data fora do mês | `{"data": ["A data precisa estar dentro de 10/2026."]}` |
| mês ou categoria inexistente ou de outra conta | `{"mes": ["Registro não encontrado."]}` (idem `categoria`) |
| forma de pagamento desconhecida | `{"forma_pagamento": ["Escolha uma forma de pagamento: dinheiro, débito, crédito ou Pix."]}` |
| mês fechado (depois dos campos) | `{"detail": "O mês 10/2026 está fechado. Reabra o mês para alterar os gastos."}` |

## `GET /api/gastos/{id}/`

**200 OK**: o gasto.

## `PATCH` / `PUT /api/gastos/{id}/`

Altera qualquer campo, com as validações do `POST`. A data é conferida contra o mês final (o
enviado ou o atual). **400** `{"detail": ...}` de mês fechado se o mês atual **ou** o de destino
estiver fechado.

## `DELETE /api/gastos/{id}/`

**204 No Content**. **400** `{"detail": ...}` de mês fechado.

## `GET /api/gastos/formas-pagamento/`

**200 OK**: `[{"codigo": "dinheiro", "nome": "Dinheiro"}, {"codigo": "debito", "nome": "Débito"},
{"codigo": "credito", "nome": "Crédito"}, {"codigo": "pix", "nome": "Pix"}]`.

## `GET /api/meses/{id}/totais/`

**200 OK**:

```json
{ "total": "223.45",
  "por_categoria": [
    { "categoria": 3, "nome": "Alimentação", "cor": "laranja", "total": "200.00", "quantidade": 2 },
    { "categoria": 5, "nome": "Transporte", "cor": "roxo", "total": "23.45", "quantidade": 1 } ] }
```

Só categorias com gastos no mês; maior total primeiro, empate em ordem alfabética. Mês sem
gastos: `{"total": "0.00", "por_categoria": []}`. Mês de outra conta: 404.

## Mudanças em rotas existentes

- `DELETE /api/meses/{id}/` (spec 007): mês com gastos → `400 {"detail": "Exclua ou mova os gastos
  antes de excluir o mês."}`.
- `DELETE /api/categorias/{id}/` (spec 006) aceita `?mover_para=<id>`:
  - sem gastos: 204 como antes;
  - com gastos e sem `mover_para` → `400 {"detail": "Esta categoria tem gastos. Escolha outra
    categoria para recebê-los."}`;
  - `mover_para` inválido (não é número, de outra conta, inexistente ou a própria) →
    `400 {"mover_para": ["Escolha outra categoria sua para receber os gastos."]}`;
  - válido → os gastos passam para o destino e a categoria é excluída (204).
