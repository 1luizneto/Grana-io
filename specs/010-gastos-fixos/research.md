# Research: Gastos Fixos

**Feature**: `010-gastos-fixos` | **Plano**: [plan.md](plan.md)

Segue as specs 004 (dono), 007 (meses), 008 (gastos, `Decimal`, service de regras) e 009 (tela).
Nenhuma dependência nova.

---

## R-01 — Model `GastoFixo` e a origem no `Gasto`

**Decisão**: `GastoFixo(OwnedModel)` em `gastos/models.py`:

- `descricao` (100), `valor` (`DecimalField(12, 2)`, `CheckConstraint` `> 0`), `forma_pagamento`
  (mesmas opções do gasto), `categoria` (FK `RESTRICT`, `related_name="fixos"`);
- `dia_vencimento` (`PositiveSmallIntegerField`, `CheckConstraint` 1 a 31);
- `inicio` e `fim` (`DateField`, sempre no dia 1; `fim` nulo = sem fim; `CheckConstraint`
  `fim >= inicio`);
- `ativo` (`BooleanField(default=True)`);
- ordem: `["dia_vencimento", "id"]` (como uma lista de contas a pagar).

`Gasto` ganha `fixo = ForeignKey(GastoFixo, null=True, blank=True, on_delete=SET_NULL,
related_name="gastos_gerados")`: excluir o fixo mantém os gastos (Clarifications), e a US-09 usa
a referência para não duplicar.

**Alternativas**: um campo "recorrente" no próprio `Gasto` (o gasto de um mês viraria modelo dos
outros; mudar o valor "só para frente" ficaria ambíguo).

---

## R-02 — Mês de início e de fim na API: texto `AAAA-MM`

**Decisão**: campo `MesAnoField` (serializer) que aceita `"2026-11"` e grava `date(2026, 11, 1)`;
responde `"2026-11"`. Erros: formato inválido → "Informe o mês no formato AAAA-MM."; ano fora de
2000 a 2100 → "Informe um ano de 2000 a 2100." (mesma faixa da spec 007). `fim` aceita `null`.

**Rationale**: é o formato do `<input type="month">` do navegador, sem conversão na tela.

---

## R-03 — Geração ao criar o mês (application service)

**Decisão**: `gastos/services/fixos.py` com `gerar_gastos_fixos(mes)`: para cada fixo ativo do
dono com `inicio <= mês` e (`fim` nulo ou `fim >= mês`), cria um `Gasto` (descrição, valor,
categoria, forma, `fixo`) na data `min(dia_vencimento, último dia do mês)`, num `bulk_create`. A
`MesReferenciaViewSet.perform_create` salva o mês e gera os gastos **na mesma transação** (o
`salvar_ou_erro_de_unicidade` já abre um `atomic`): ou vem o mês com os fixos, ou nada.

**Rationale**: o `docs/arquitetura.md` prevê um caso de uso "criar mês" para a US-07b e a US-09;
começa como função (`criar mês` = salvar + gerar), sem classe, até a US-09 precisar de mais passos.

---

## R-04 — "Repetir todo mês" no lançamento

**Decisão**: `POST /api/gastos/` aceita `"repetir": true` (só escrita, só na criação). A view, numa
transação, salva o gasto e chama `criar_fixo_do_gasto(gasto)`, que cria o fixo (mesmos dados;
`dia_vencimento = data.day`; `inicio = mês do gasto`) e liga o gasto a ele (`gasto.fixo`). Em
`PATCH`/`PUT`, `repetir` é ignorado.

**Rationale**: atende "marcar um gasto como recorrente, com dia de vencimento" num passo só, e o
mês atual não ganha um gasto duplicado (a geração só roda em meses novos).

---

## R-05 — Categoria excluída leva os fixos

**Decisão**: `excluir_categoria` (spec 008) passa a considerar gastos **ou** fixos: sem destino e
com qualquer um deles → a mesma recusa; com destino, move os dois e exclui.

---

## R-06 — API `/api/fixos/`

**Decisão**: `GastoFixoViewSet(FiltroPorDonoMixin, ModelViewSet)`, rota `fixos` (pt-BR, plural,
curta). Representação: `{id, descricao, valor, categoria, forma_pagamento, dia_vencimento, inicio,
fim, ativo}`. Desativar/reativar = `PATCH {"ativo": false|true}`. Mensagens: as do gasto (spec 008)
para descrição, valor, categoria e forma; dia → "Informe um dia de 1 a 31."; fim antes do início →
`{"fim": ["O mês de fim precisa ser igual ou posterior ao de início."]}`.

---

## R-07 — Gasto mostra a origem

**Decisão**: a representação do gasto ganha `"fixo": <id> | null` (só leitura). A tabela da tela
do mês mostra a marca "fixo" ao lado da descrição dos gastos gerados.

---

## R-08 — Tela "Gastos fixos" (`/fixos`)

**Decisão**: menu "Início", "Gastos do mês", **"Gastos fixos"**, "Categorias". Formulário no topo
("Novo gasto fixo" / "Editar gasto fixo", como o de gastos da spec 009): Descrição, Valor, Dia de
vencimento, Categoria, Forma de pagamento, Início (`type="month"`, padrão: mês de hoje) e Fim
(`type="month"`, opcional). Lista: descrição, valor, "dia N", categoria, período ("desde 11/2026"
ou "de 11/2026 a 01/2027") e "Inativo" quando for o caso; botões "Editar X", "Desativar X" /
"Reativar X" e "Excluir X" (confirmação `Excluir o gasto fixo "X"? Os gastos já lançados
continuam.`).

No formulário de gasto da tela do mês (só ao lançar), a caixa **"Repetir todo mês"**; com ela, o
retorno é "Gasto lançado e cadastrado como fixo.".

---

## Resumo de dependências

Nenhuma dependência nova.
