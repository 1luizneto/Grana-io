# Research: Lançar, Editar e Excluir Gastos

**Feature**: `008-lancar-gastos` | **Plano**: [plan.md](plan.md)

Segue a regra de dono da spec 004, os padrões de API das specs 006 e 007 e o
[docs/arquitetura.md](../../docs/arquitetura.md) (regra com mais de um model → service). Nenhuma
dependência nova.

---

## R-01 — Model `Gasto` no app `gastos`

**Decisão**: `Gasto(OwnedModel)` em `gastos/models.py`:

- `descricao = CharField(max_length=100)`;
- `valor = DecimalField(max_digits=12, decimal_places=2)` com `CheckConstraint` `valor > 0`
  (`gastos_gasto_valor_positivo`);
- `data = DateField()`;
- `forma_pagamento = CharField(max_length=10, choices=FORMAS_PAGAMENTO, blank=True, default="")`;
- `mes = ForeignKey(MesReferencia, on_delete=RESTRICT, related_name="gastos")`;
- `categoria = ForeignKey(Categoria, on_delete=RESTRICT, related_name="gastos")`;
- `ordering = ["data", "id"]` (FR-005: por data e, na mesma data, por lançamento).

**Rationale**: `RESTRICT` (e não `PROTECT`) impede excluir mês ou categoria com gastos pelo banco
(SC-005), mas deixa a exclusão da conta apagar tudo em cascata: o `RESTRICT` libera quando o gasto
também está sendo apagado pela mesma cascata (o dono), o `PROTECT` não libera nunca.

**Alternativas**: `SET_NULL` na categoria (deixaria gastos sem categoria, contra a FR-010);
`CASCADE` no mês (apagaria gastos ao excluir o mês, contra a FR-009).

---

## R-02 — Dinheiro: `Decimal`, 2 casas, `ROUND_HALF_UP` (RNF-03)

**Decisão**: módulo `core/dinheiro.py` com `CENTAVO = Decimal("0.01")` e
`arredondar(valor) -> Decimal` (`quantize(CENTAVO, ROUND_HALF_UP)`). É a regra única da
constituição (Princípio III); os totais passam por ela para sair sempre com 2 casas. A API aceita
números ou texto com **ponto** e devolve o valor como texto (`"150.30"`), padrão do DRF para
`Decimal`, sem perda de precisão no JSON.

**Validação do valor** (`DecimalField(max_digits=12, decimal_places=2, min_value=0.01)`):

| Situação | Mensagem |
|---|---|
| ausente, vazio ou nulo | "Este campo é obrigatório." |
| não numérico (`"abc"`, `"12,50"`, `NaN`) | "Informe um valor numérico, como 12.50." |
| zero ou negativo | "Informe um valor maior que zero." |
| mais de 2 casas | "Use no máximo 2 casas decimais." |
| acima de 9999999999.99 | "Informe um valor de até 9999999999.99." |

**Rationale**: recusar mais de 2 casas (em vez de arredondar) não muda o valor em silêncio
(Clarifications). O módulo fica no `core` porque cenários (EP-03) e parcelas (US-10) vão usar a
mesma regra.

---

## R-03 — Regras com mais de um model em `gastos/services/gastos.py`

**Decisão**: um módulo de service com as regras que cruzam gasto, mês e categoria, sem depender
de HTTP (docs/arquitetura.md):

- `RegraViolada(Exception)`: erro de negócio com a mensagem para a pessoa;
- `exigir_mes_aberto(*meses)`: lança `RegraViolada("O mês 10/2026 está fechado. Reabra o mês para
  alterar os gastos.")` para o primeiro mês fechado (FR-008);
- `verificar_exclusao_do_mes(mes)`: mês fechado (spec 007) e mês com gastos (FR-009);
- `excluir_categoria(categoria, destino)`: com gastos e sem destino → `RegraViolada`; com destino,
  move os gastos e exclui, em `transaction.atomic()` (FR-010);
- `totais_do_mes(mes)`: total do mês e por categoria (FR-006).

As views traduzem `RegraViolada` para `400 {"detail": "<mensagem>"}` (mesmo formato da spec 007,
que a interface já mostra como mensagem geral). A regra de mês fechado da spec 007, hoje na view,
passa para `verificar_exclusao_do_mes`.

**Rationale**: as regras envolvem mais de um model, e a US-07b, a US-09 e a US-10 vão reaproveitar
`exigir_mes_aberto`.

---

## R-04 — Onde cada regra roda no fluxo da API

| Regra | Onde | Resposta |
|---|---|---|
| campos (valor, data, descrição, forma) | serializer | 400 por campo |
| mês/categoria de outra conta | `RelacionadoDoDonoField` | 400 "Registro não encontrado." no campo |
| data dentro do mês | `GastoSerializer.validate` (usa o mês enviado ou o atual) | 400 no campo `data` |
| mês fechado (criar, alterar, mover, excluir) | view → `exigir_mes_aberto` | 400 `{"detail"}` |

O mês fechado é conferido depois da validação de campos: um envio com campos errados num mês
fechado recebe primeiro os erros de campo. É aceitável e mantém o serializer sem regra de dois
models.

---

## R-05 — Lista com filtros `?mes=` e `?categoria=`

**Decisão**: `GET /api/gastos/` lista os gastos da pessoa; `?mes=<id>` e `?categoria=<id>` filtram
(a US-27 filtra por categoria). Identificador que não é número → `400 {"mes": ["Informe o número
do mês."]}` (idem `categoria`); número de outra conta → lista vazia (o filtro roda depois do filtro
por dono, sem revelar nada). Sem paginação: dezenas a centenas de gastos por mês.

**Alternativas**: rota aninhada `/api/meses/{id}/gastos/` (mais um nível de rota e de testes de
isolamento, sem ganho); `django-filter` (dependência nova para dois filtros).

---

## R-06 — Totais em `GET /api/meses/{id}/totais/`

**Decisão**: ação na viewset de meses, que já garante o 404 de mês de outra conta:

```json
{ "total": "223.45",
  "por_categoria": [ { "categoria": 3, "nome": "Alimentação", "cor": "laranja", "total": "200.00", "quantidade": 2 } ] }
```

`por_categoria` traz só categorias com gastos no mês, do maior total para o menor e, empatando,
em ordem alfabética. Cálculo com `Sum` no banco (`Decimal` exato) e `arredondar` na saída.

---

## R-07 — Excluir categoria com destino: `DELETE /api/categorias/{id}/?mover_para=<id>`

**Decisão**: parâmetro de consulta (um `DELETE` com corpo é mal suportado por clientes HTTP).

- sem gastos: exclui, com ou sem `mover_para` (spec 006 continua valendo);
- com gastos e sem `mover_para` → `400 {"detail": "Esta categoria tem gastos. Escolha outra
  categoria para recebê-los."}`;
- `mover_para` que não é categoria da pessoa, ou é a própria → `400 {"mover_para": ["Escolha outra
  categoria sua para receber os gastos."]}`;
- válido → move os gastos (inclusive de meses fechados, Clarifications) e exclui, tudo ou nada.

---

## R-08 — Formas de pagamento

**Decisão**: `FORMAS_PAGAMENTO = [("dinheiro", "Dinheiro"), ("debito", "Débito"), ("credito",
"Crédito"), ("pix", "Pix")]` em `gastos/models.py`; `GET /api/gastos/formas-pagamento/` devolve
`[{"codigo", "nome"}]` (como a paleta de cores, spec 006), para a tela não repetir a lista. Sem
forma: `""` na resposta; a API aceita ausente, `""` ou `null`. Código desconhecido → "Escolha uma
forma de pagamento: dinheiro, débito, crédito ou Pix.".

---

## R-09 — Kit de isolamento com referências

**Decisão**: o `payload_criacao` do kit é fixo, mas um gasto precisa de mês e categoria **da Ana**,
criados no teste. O kit ganha o gancho `montar_payload_criacao(usuario)`, que por padrão devolve
`payload_criacao`; a subclasse de gastos o sobrescreve criando o mês e a categoria da Ana. As
subclasses existentes não mudam.

---

## Resumo de dependências

Nenhuma dependência nova.
