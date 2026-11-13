# Research: Tela do Mês

**Feature**: `009-tela-mes` | **Plano**: [plan.md](plan.md)

Segue os padrões de tela das specs 005 e 006 (erros da API exibidos como chegam, hooks por
recurso, componentes de apresentação) e o [docs/arquitetura.md](../../docs/arquitetura.md) §3.
Usa só a API das specs 006 a 008. Nenhuma dependência nova.

---

## R-01 — Rotas `/meses` e `/meses/:id`

**Decisão**: a tela fica em `/meses/:id`. `/meses` escolhe o mês inicial (FR-003: mês de hoje, se
existir; senão o último da lista da API) e redireciona com `replace` para `/meses/:id`; sem meses,
fica em `/meses` com o estado vazio. Menu "Gastos do mês" → `/meses` (o `NavLink` fica ativo também
em `/meses/:id`). Id que não está na lista da pessoa → "Mês não encontrado.".

**Rationale**: o mês no endereço sobrevive a recarregar e permite voltar com o botão do navegador
(FR-002).

---

## R-02 — Hooks e módulos de API

- `api/meses.js`: `listarMeses`, `criarMes`, `atualizarMes` (PATCH `fechado`), `excluirMes`,
  `buscarTotais`.
- `api/gastos.js`: `listarGastos(mesId)` (`?mes=`), `criarGasto`, `atualizarGasto` (PATCH),
  `excluirGasto`, `listarFormasPagamento`.
- `api/categorias.js`: `excluirCategoria(id, moverPara)` passa `?mover_para=` quando houver.
- `hooks/useMeses.js`: lista de meses + criar, fechar/reabrir e excluir (recarrega a lista).
- `hooks/useGastosDoMes.js`: gastos e totais do mês (em paralelo) + criar, atualizar e excluir
  (recarregam os dois); formas de pagamento carregadas uma vez.
- Categorias e cores: o `useCategorias` da spec 006 (as cores dão o `hex` dos totais).

Todas as ações devolvem `{ok}` ou `{ok: false, erro}` (com `interpretarErro`), como o
`useCategorias`.

---

## R-03 — Formatação e conversão sem cálculo (`utils/formatacao.js`)

| Função | Exemplo |
|---|---|
| `formatarMoeda("1234.50")` | `"R$ 1.234,50"` (manipulação de texto, sem `Number`) |
| `formatarData("2026-10-05")` | `"05/10/2026"` |
| `paraValorDaApi("1.234,56")` | `"1234.56"`; `"12,5"` → `"12.5"`; `"12.50"` → `"12.50"`; espaços removidos |
| `emCentavos("150.30")` | `15030n` (`BigInt`, só para ordenar por valor) |

**Rationale**: o Princípio V e o RNF-03 proíbem a tela de calcular valores; formatar e comparar
para ordenar não alteram valores, e o `BigInt` evita qualquer arredondamento de ponto flutuante.
`paraValorDaApi` não valida: valores estranhos vão para a API, que responde com a mensagem do
campo.

---

## R-04 — Filtro e ordenação na tela

**Decisão**: sobre a lista do mês já carregada (ordem da API: data e lançamento). Filtro: "Todas as
categorias" + as categorias da pessoa. Ordem: "Data (mais antigo)" (a da API), "Data (mais
recente)" (a da API invertida), "Maior valor" e "Menor valor" (por `emCentavos`, ordenação estável).

**Alternativas**: parâmetros de ordenação na API (mais código no backend para uma escolha de
exibição; o filtro por categoria da API, spec 008, continua disponível para outros usos).

---

## R-05 — Formulário rápido de gasto (criar e editar)

**Decisão**: um único `FormularioGasto` no topo da lista: "Descrição", "Valor" (texto, teclado
decimal), "Data" (`type="date"` com `min`/`max` do mês), "Categoria" (`select`, começa em "Escolha
uma categoria"), "Forma de pagamento" (`select`, "Não informar" + as formas da API).

- **Criar**: botão "Lançar" ("Lançando…"); no sucesso, "Gasto lançado.", limpa descrição, valor e
  forma, mantém data e categoria (lançar vários seguidos) e devolve o foco à descrição.
- **Editar**: "Editar <descrição>" na tabela carrega o gasto no formulário (título "Editar gasto"),
  com "Salvar alterações" e "Cancelar edição".
- Erros de campo ao lado de cada campo; `detail` (mês fechado) como mensagem geral.
- Data padrão: hoje, se estiver no mês; senão o dia 1.

**Rationale**: um formulário só (e não edição na linha da tabela) cabe na tela estreita e
reaproveita validação e mensagens.

---

## R-06 — Seletor e criação de mês

**Decisão**: `select` "Mês" com os rótulos da API (fechados com " (fechado)"). Formulário "Novo
mês": `select` "Mês" (Janeiro a Dezembro) e campo "Ano"; padrão = o mês seguinte ao mais recente
(ou o de hoje, sem meses). Ao criar, navega para o mês novo.

---

## R-07 — Retorno das operações

**Decisão**: mensagem de sucesso num `p role="status"` (anunciada sem interromper), trocada a cada
operação; erros em `role="alert"` (`AvisoFormulario`, que ganha o tipo `sucesso` com
`role="status"`).

---

## R-08 — Confirmações

**Decisão**: excluir gasto e excluir mês com `window.confirm`, como a spec 006:
`Excluir o gasto "Mercado" de R$ 150,30?` e `Excluir o mês 11/2026?`.

---

## R-09 — Excluir categoria com destino (tela de categorias)

**Decisão**: o `window.confirm` da spec 006 vira um painel na linha: "Excluir a categoria
"Lazer"?", `select` "Mover os gastos para" (as outras categorias, com "Outros" escolhida se
existir, senão a primeira) e os botões "Excluir" e "Cancelar". O envio sempre leva
`?mover_para=<escolhida>`; sem gastos, a API ignora o destino. Se não houver outra categoria, o
painel diz "Não há outra categoria para receber gastos." e envia sem destino (a API recusa se
houver gastos).

**Rationale**: a tela não sabe se a categoria tem gastos; perguntar sempre é simples e o destino é
inofensivo quando não há gastos.

---

## R-10 — Tela estreita

**Decisão**: abaixo de 640 px, a tabela vira cartões (`display: block` nas linhas, rótulo de cada
célula por `data-rotulo` + `::before`), os formulários ficam em coluna e os totais em lista.

---

## Resumo de dependências

Nenhuma dependência nova.
