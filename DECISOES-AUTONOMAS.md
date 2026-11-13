# Decisões tomadas em modo autônomo

Em 2026-11-13 o responsável pediu: "vai continuando o projeto até onde der, vai tomando as
decisões, faz um arquivo só com isso pra depois eu olhar". Este arquivo é esse registro.

**Como ler**: cada decisão diz o que foi escolhido, por quê e onde ficou. As marcadas com ⚠️ são
as que mais valem uma conferida, porque mudam comportamento visível ou escopo.

## Como o trabalho foi conduzido

- Mesmo fluxo de sempre (spec-kit: specify → clarify → plan → tasks → analyze → implement), com
  commit + push a cada checkpoint, mensagens em pt-BR e sem trailers de IA.
- **Sem paradas**: nas perguntas do clarify e nos achados do analyze, escolhi eu (normalmente a
  opção recomendada) e anotei aqui.
- **PR e merge continuam com você.** Como as specs dependem umas das outras, cada branch nova sai
  da anterior (branches empilhadas). **Ordem de merge** na tabela abaixo: abra os PRs nessa
  ordem; depois do merge de uma, o PR da seguinte mostra só as mudanças dela.

## Branches e ordem de merge

| Ordem | Branch | US | Situação |
|---|---|---|---|
| 1 | `007-mes-referencia` | US-06 | Pronta para PR na `main` (20/20 tarefas) |
| 2 | `008-lancar-gastos` | US-07 + US-08 (API) | Pronta para PR depois da 007 (28/28 tarefas) |
| 3 | `009-tela-mes` | US-27 (tela do mês) | Pronta para PR depois da 008 (22/22 tarefas) |
| 4 | `010-gastos-fixos` | US-07b (gastos fixos) | Pronta para PR depois da 009 (19/19 tarefas) |

---

## Spec 007 — Mês de referência (US-06)

O specify, o clarify, o plan e as Phases 1 a 6 foram feitos com você acompanhando. Em modo
autônomo, só a Phase 7 (Polish).

- **D-007-1**: no BACKLOG, os 4 critérios da US-06 ficaram ☑. O 4º ("fechado bloqueia edições")
  tem nota: hoje o fechado só impede excluir o mês; o bloqueio dos gastos chega com a US-07 e a
  US-08.
- **D-007-2**: a US-07 ganhou dois critérios herdados: "mês fechado não aceita novos gastos" e
  "mês com gastos não pode ser excluído".

---

## Spec 008 — Lançar, editar e excluir gastos (US-07 + US-08)

Fluxo completo em modo autônomo: specify, clarify, plan, tasks, analyze e implement.

**Escopo**

- **D-008-1** ⚠️: a US-07 e a US-08 ficaram **numa spec só**. O kit de isolamento já exige abrir,
  alterar e excluir todo registro novo, e a regra do mês fechado vale para as três operações;
  separar duplicaria quase tudo.
- **D-008-2**: **só API**, como na 007. A tela do mês (formulário, lista, confirmação antes de
  excluir) e a escolha do destino na tela de categorias ficam para a próxima spec (US-27). Por
  isso o critério "há confirmação antes de excluir" da US-08 continua ☐.
- **D-008-3**: os dois primeiros critérios do RNF-03 (Decimal; regra de arredondamento) entraram
  aqui, porque é a primeira spec com dinheiro. O 3º (frontend não recalcula) fica com a US-27.

**Regras de negócio**

- **D-008-4** ⚠️: valor com **mais de 2 casas é recusado** ("Use no máximo 2 casas decimais."),
  não arredondado. Arredondar mudaria o valor digitado sem avisar.
- **D-008-5**: a **API usa ponto** decimal (`"150.30"`); "12,50" é recusado como não numérico. A
  tela da US-27 vai aceitar vírgula e converter.
- **D-008-6**: limite do valor em 9.999.999.999,99 (12 dígitos).
- **D-008-7** ⚠️: ao excluir uma categoria com gastos, os gastos de **meses fechados também são
  movidos** para a categoria destino. O total do mês não muda; exigir reabrir cada mês fechado
  tornaria a exclusão impraticável.
- **D-008-8**: o destino vai como parâmetro de consulta, `DELETE /api/categorias/<id>/?mover_para=<id>`
  (DELETE com corpo é mal suportado por clientes HTTP).
- **D-008-9**: o mês fechado bloqueia também **mover** um gasto para ele ou para fora dele.
- **D-008-10**: forma de pagamento sem valor é `""` (aceita ausente, `""` ou `null`); a lista de
  formas vem da API em `/api/gastos/formas-pagamento/`, como a paleta de cores.
- **D-008-11**: erros de campo aparecem antes do erro de mês fechado (o mês fechado é conferido
  depois da validação). Mantém o serializer sem regra de dois modelos.

**Técnicas**

- **D-008-12**: `RESTRICT` (não `PROTECT`) nas chaves de mês e categoria: impede apagar mês ou
  categoria com gastos, mas deixa a exclusão da conta apagar tudo. Testado.
- **D-008-13**: regras que cruzam modelos em `gastos/services/gastos.py` (`RegraViolada`), como
  manda o `docs/arquitetura.md`; a regra de mês fechado da spec 007 foi para lá também.
- **D-008-14**: totais em `GET /api/meses/<id>/totais/` (maior total primeiro; empate em ordem
  alfabética). Lista de gastos com filtros `?mes=` e `?categoria=`, sem paginação.
- **D-008-15**: o kit de isolamento ganhou o gancho `montar_payload_criacao(usuario)`, porque o
  payload de um gasto precisa do mês e da categoria da própria pessoa.
- **D-008-16**: `core/dinheiro.py` com `arredondar` (ROUND_HALF_UP, 2 casas), no `core` porque
  cenários e parcelas vão usar a mesma regra.

**Resultado**: backend 387 testes, interface 85. Quickstart S1 a S7 validado com `curl`; banco
local deixado sem gastos e meses de teste (a categoria Lazer da Ana foi recriada, com outro id).

---

## Spec 009 — Tela do mês (US-27)

Fluxo completo em modo autônomo, com validação no navegador embutido (conta de teste
`teste.s9@exemplo.com`, criada pela tela de cadastro; os gastos e o mês de teste foram excluídos
no fim, e a conta ficou).

**Escopo**

- **D-009-1**: a tela entrou com as pendências de tela das specs 007 e 008: confirmação antes de
  excluir gasto (US-08), destino dos gastos ao excluir categoria (US-05/US-07) e "o frontend não
  recalcula" (RNF-03).
- **D-009-2** ⚠️: **recorrentes e parcelados** ainda **não** estão no formulário (as US-07b e US-10
  não existem na API). O critério da US-27 ficou ☐, com nota. "Copiar do mês anterior" fica com a
  US-09.

**Comportamento**

- **D-009-3**: a tela abre no **mês de hoje**; se ele não existir, no mais recente. O mês fica no
  endereço (`/meses/<id>`), então recarregar ou voltar mantém o mês.
- **D-009-4**: "Novo mês" sugere o **mês seguinte ao mais recente** (ou o de hoje, se não houver
  meses).
- **D-009-5** ⚠️: o **valor aceita a escrita brasileira**: "1.234,56" vira "1234.56". Com vírgula,
  os pontos são milhar; sem vírgula, o ponto é o decimal ("12.50" continua 12,50).
- **D-009-6**: depois de lançar, o formulário **mantém a data e a categoria** e limpa o resto, para
  lançar vários seguidos; o foco volta à descrição.
- **D-009-7**: editar usa o **mesmo formulário** do topo (e não edição na linha da tabela), que
  cabe melhor no celular.
- **D-009-8**: filtro e ordenação rodam na tela, sobre a lista do mês; comparar valores usa
  centavos inteiros (`BigInt`), sem ponto flutuante.
- **D-009-9** ⚠️: na tela de categorias, o `window.confirm` virou um **painel na linha** com "Mover
  os gastos para" ("Outros" escolhida quando existe). O destino é enviado sempre; a API o ignora
  se a categoria não tiver gastos.
- **D-009-10**: com o mês fechado, o formulário fica desabilitado e a tabela perde os botões de
  editar e excluir; um aviso fixo explica como reabrir.
- **D-009-11**: menu "Início", **"Gastos do mês"**, "Categorias"; a página inicial ganhou um link
  para a tela do mês. Rótulos "Escolher mês" e "Filtrar por categoria", para não repetir os
  campos "Mês" e "Categoria" dos formulários.

**Achados da validação no navegador (corrigidos, com teste)**

- **D-009-12**: a mensagem de sucesso anterior ("Gasto lançado.") ficava na tela durante um erro
  novo. Agora cada operação apaga a mensagem da anterior.
- **D-009-13**: com a categoria vazia, a API respondia "Este campo pode não ser nulo." (texto
  padrão do DRF). O `RelacionadoDoDonoField` (spec 004) agora responde "Este campo é
  obrigatório." para `null`. É uma mudança pequena no backend dentro de uma spec de tela.

**Resultado**: backend 388 testes, interface 140. Navegador: S2 a S8 conferidos, inclusive
lançamento em 8,9 s com automação (SC-001: até 30 s), 360 px sem rolagem horizontal (tabela em
cartões) e lançamento só pelo teclado.

---

## Spec 010 — Gastos fixos (US-07b)

Fluxo completo em modo autônomo, com validação no navegador (conta `teste.s9@exemplo.com`; dados
de teste excluídos no fim).

**Comportamento**

- **D-010-1** ⚠️: "marcar um gasto como recorrente" virou **dois caminhos**: a caixa **"Repetir
  todo mês"** ao lançar (o vencimento é o dia da data; começa no mês do gasto) e a tela própria
  **"Gastos fixos"** (menu entre "Gastos do mês" e "Categorias"), onde se cadastra, altera,
  encerra, desativa e exclui.
- **D-010-2** ⚠️: os fixos só entram em meses **criados depois**. Criar ou mudar um fixo não mexe
  em meses existentes (é o critério "só nos meses seguintes"). Se você quiser o fixo num mês que
  já existe, lance o gasto nele (pode ser com "Repetir todo mês").
- **D-010-3**: vencimento que não existe no mês (31 em novembro, 30 em fevereiro) cai no **último
  dia** do mês.
- **D-010-4**: excluir um fixo **mantém** os gastos já lançados (viram gastos comuns, sem a marca
  "fixo").
- **D-010-5**: excluir uma categoria trata os fixos como gastos: exige o destino e move os dois.
- **D-010-6**: os gastos gerados mostram a marca **"fixo"** na tabela do mês; editar ou excluir
  esse gasto não muda o fixo.

**Técnicas**

- **D-010-7**: model próprio `GastoFixo` (não um campo no gasto) e `Gasto.fixo` como origem
  (`SET_NULL`). A US-09 (copiar mês) vai usar essa origem para não duplicar os fixos.
- **D-010-8**: meses de início e de fim como texto `AAAA-MM` na API (o formato do
  `<input type="month">`), gravados como o dia 1.
- **D-010-9**: o mês é criado com os gastos fixos **na mesma transação**; "Repetir todo mês" cria
  gasto e fixo também numa transação só (testado com falhas simuladas).
- **D-010-10**: campos e mensagens comuns de gasto e fixo numa base de serializer, para os dois
  responderem igual.

**Resultado**: backend 449 testes, interface 152. Navegador: cadastro com erros de dia e de fim;
mês novo com o Aluguel; "Repetir todo mês"; 12/2026 e 02/2027 gerados (dia 30 → 28/02); reajuste
só para frente; desativar; excluir mantendo os gastos; 360 px sem rolagem; Bia → 404.
