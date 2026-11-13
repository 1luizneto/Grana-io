# Feature Specification: Tela do Mês

**Feature Branch**: `009-tela-mes`

**Created**: 2026-11-13

**Status**: Draft

**Input**: User description: "US-27: Como usuário, quero uma tela do mês com os lançamentos, para cadastrar e revisar meus gastos. Critérios: um seletor de mês permite criar novos meses (US-06, US-09); uma tabela de gastos permite filtrar por categoria e ordenar por data e valor; um formulário rápido cria e edita gastos (US-07, US-08), incluindo recorrentes e parcelados; totais por categoria e o total do mês ficam visíveis na tela; há feedback claro de sucesso e de erro nas operações. Inclui as pendências de tela das specs 007 e 008: confirmação antes de excluir gasto (US-08), escolher a categoria que recebe os gastos ao excluir uma categoria (US-05/US-07) e o frontend não refazer cálculos financeiros (RNF-03)."

## Clarifications

### Session 2026-11-13

> Sessão respondida em modo autônomo (ver `DECISOES-AUTONOMAS.md`, D-009-*).

- Q: Qual mês a tela abre? → A: O mês do dia de hoje, se existir; senão o mais recente; sem meses,
  a tela mostra só o formulário de novo mês.
- Q: Recorrentes e parcelados entram no formulário agora? → A: Não. As US-07b e US-10 ainda não
  existem na API; o formulário ganha esses campos nas specs delas. O critério fica anotado.
- Q: Ao excluir uma categoria, como a pessoa escolhe o destino dos gastos? → A: A confirmação de
  exclusão vira um painel na própria linha, com a pergunta "Mover os gastos para" (as outras
  categorias, já com "Outros" escolhida quando existir). Se a categoria não tiver gastos, o destino
  é ignorado.
- Q: Como o valor é digitado? → A: Como no Brasil: "1.234,56" ou "12,50". Também aceita "12.50".
  Com vírgula, os pontos são separadores de milhar; sem vírgula, o ponto é o decimal.

## User Scenarios & Testing *(mandatory)*

> **Contexto**: as specs 007 e 008 entregaram meses, gastos e totais pela API. Esta spec entrega a
> tela que a pessoa usa no dia a dia. A tela só formata e exibe: totais, validações e regras vêm
> da API (Princípio V; RNF-03).

### User Story 1 - Escolher e criar o mês (Priority: P1)

A pessoa abre "Gastos do mês", vê o mês atual (ou o mais recente) e troca de mês num seletor. Pode
criar um mês novo informando mês e ano.

**Why this priority**: sem escolher o mês não há onde lançar.

**Independent Test**: com 09/2026 e 10/2026 criados, abrir a tela (hoje em outubro de 2026) e ver
10/2026; trocar para 09/2026; criar 11/2026 e ver a tela já nele.

**Acceptance Scenarios**:

1. **Given** os meses 09/2026 e 10/2026 e hoje em 10/2026, **When** a pessoa abre a tela, **Then** vê 10/2026 selecionado.
2. **Given** hoje em 12/2026 e só 09/2026 e 10/2026 criados, **When** abre a tela, **Then** vê 10/2026 (o mais recente).
3. **Given** nenhum mês, **When** abre a tela, **Then** vê "Nenhum mês criado. Crie o primeiro abaixo." e o formulário de novo mês.
4. **Given** o formulário de novo mês, **When** cria 11/2026, **Then** a tela passa a mostrar 11/2026.
5. **Given** um mês repetido, **When** tenta criá-lo, **Then** vê "Este mês já foi criado." e nada muda.
6. **Given** o seletor, **When** a pessoa escolhe outro mês, **Then** o endereço da página muda e recarregar mantém o mês.

---

### User Story 2 - Lançar gastos e ver os totais (Priority: P1)

No mês escolhido, a pessoa lança um gasto pelo formulário rápido e vê a lista e os totais
atualizados.

**Why this priority**: é o uso principal do sistema.

**Independent Test**: lançar "Mercado", "150,30", Alimentação, Pix e ver a linha na tabela, o total
do mês "R$ 150,30" e o total de Alimentação.

**Acceptance Scenarios**:

1. **Given** o mês 10/2026 aberto, **When** a pessoa lança "Mercado", "150,30", Alimentação, Pix, **Then** vê "Gasto lançado.", a linha na tabela com "R$ 150,30" e os totais atualizados, e o formulário pronto para o próximo (mantendo data e categoria).
2. **Given** valor "0" ou data fora do mês, **When** tenta lançar, **Then** vê a mensagem da API ao lado do campo e o que digitou continua lá.
3. **Given** um mês com gastos, **When** a pessoa abre o mês, **Then** vê o total do mês e, por categoria, a cor, o nome, o total e a quantidade, como a API calculou.
4. **Given** um mês sem gastos, **When** abre, **Then** vê "Nenhum gasto neste mês." e total "R$ 0,00".

---

### User Story 3 - Corrigir e excluir gastos (Priority: P2)

A pessoa edita um gasto pelo mesmo formulário e exclui com confirmação.

**Why this priority**: corrigir erros mantém os totais confiáveis (US-08).

**Independent Test**: editar o valor de um gasto e ver o total mudar; excluir confirmando e ver
sumir; cancelar a confirmação e ver que fica.

**Acceptance Scenarios**:

1. **Given** um gasto, **When** a pessoa clica "Editar Mercado", **Then** o formulário mostra os dados dele, com "Salvar alterações" e "Cancelar edição".
2. **Given** a edição, **When** salva, **Then** vê "Gasto atualizado." e a tabela e os totais mudam.
3. **Given** um gasto, **When** clica "Excluir Mercado", **Then** é perguntada `Excluir o gasto "Mercado" de R$ 150,30?`; cancelando, nada muda; confirmando, vê "Gasto excluído." e ele some.

---

### User Story 4 - Filtrar e ordenar a tabela (Priority: P2)

A pessoa filtra os gastos por categoria e ordena por data ou valor.

**Why this priority**: revisar um mês cheio fica mais fácil.

**Independent Test**: com gastos em 2 categorias, filtrar por uma e ver só os dela; ordenar por
maior valor.

**Acceptance Scenarios**:

1. **Given** gastos em Alimentação e Transporte, **When** a pessoa escolhe "Transporte" no filtro, **Then** vê só os de Transporte; "Todas as categorias" volta a mostrar todos.
2. **Given** gastos, **When** escolhe "Maior valor", **Then** a tabela fica do maior para o menor valor; "Data (mais antigo)" volta à ordem da API.
3. **Given** um filtro sem gastos, **Then** vê "Nenhum gasto nesta categoria."

---

### User Story 5 - Fechar, reabrir e excluir o mês (Priority: P2)

A pessoa fecha o mês revisado, reabre se precisar e exclui um mês criado por engano.

**Why this priority**: dá tela às regras da spec 007.

**Independent Test**: fechar o mês e ver o formulário e as ações de gasto desabilitados; reabrir;
excluir um mês vazio.

**Acceptance Scenarios**:

1. **Given** o mês aberto, **When** clica "Fechar mês", **Then** vê "Mês fechado. Reabra o mês para lançar ou alterar gastos.", o formulário desabilitado e sem os botões de editar e excluir gastos.
2. **Given** o mês fechado, **When** clica "Reabrir mês", **Then** tudo volta a funcionar.
3. **Given** um mês aberto sem gastos, **When** clica "Excluir mês" e confirma `Excluir o mês 11/2026?`, **Then** o mês some e a tela mostra outro mês (ou o estado vazio).
4. **Given** um mês com gastos, **When** tenta excluir, **Then** vê "Exclua ou mova os gastos antes de excluir o mês."

---

### User Story 6 - Excluir categoria escolhendo o destino dos gastos (Priority: P2)

Na tela de categorias, a pessoa exclui uma categoria e escolhe para onde vão os gastos dela.

**Why this priority**: sem isso, uma categoria com gastos não pode ser excluída pela tela.

**Independent Test**: excluir Lazer (com gastos) escolhendo Outros e ver os gastos em Outros na
tela do mês.

**Acceptance Scenarios**:

1. **Given** a lista de categorias, **When** clica "Excluir Lazer", **Then** a linha mostra "Excluir a categoria "Lazer"?", o seletor "Mover os gastos para" (as outras categorias; "Outros" já escolhida) e os botões "Excluir" e "Cancelar".
2. **Given** o painel, **When** confirma, **Then** a categoria some e os gastos dela passam para a escolhida.
3. **Given** o painel, **When** cancela, **Then** nada muda.
4. **Given** a única categoria da conta, **When** tenta excluir, **Then** o painel avisa que não há outra categoria para receber gastos e a exclusão segue só se a API aceitar (sem gastos).

---

### Edge Cases

- **Sessão expira durante o uso**: o comportamento da spec 005 (volta ao login com aviso).
- **Endereço com mês de outra pessoa ou inexistente** (`/meses/999`): "Mês não encontrado." e o
  seletor para escolher outro.
- **Falha de rede**: "Não foi possível falar com o servidor. Tente novamente." e o que foi digitado
  continua.
- **Valor com vírgula e milhar** ("1.234,56"): enviado como "1234.56".
- **Tela estreita (360 px)**: sem rolagem horizontal; a tabela vira lista de cartões.
- **Envio duplo**: botões desabilitados enquanto a operação está em andamento.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A tela "Gastos do mês" MUST ficar no menu, depois de "Início", e exigir sessão.
- **FR-002**: Um seletor MUST listar os meses da pessoa (MM/AAAA, ordem cronológica da API) e trocar o mês exibido; o mês escolhido MUST ficar no endereço da página.
- **FR-003**: Sem mês no endereço, a tela MUST abrir no mês de hoje, se existir, ou no mais recente.
- **FR-004**: Um formulário MUST criar meses (mês e ano), exibindo os erros da API.
- **FR-005**: Um formulário rápido MUST lançar gastos (descrição, valor, data, categoria, forma de pagamento opcional) e editar gastos, exibindo os erros de campo ao lado de cada campo.
- **FR-006**: O valor MUST aceitar a escrita brasileira ("1.234,56") e ser enviado com ponto decimal, sem cálculos.
- **FR-007**: A tabela MUST mostrar data (DD/MM/AAAA), descrição, categoria, forma de pagamento e valor (R$), com filtro por categoria e ordenação por data e valor.
- **FR-008**: O total do mês e os totais por categoria MUST vir da API e ser exibidos sem recalcular (RNF-03).
- **FR-009**: Excluir gasto e excluir mês MUST pedir confirmação.
- **FR-010**: Fechar e reabrir o mês MUST estar na tela; com o mês fechado, lançar, editar e excluir gastos MUST ficar indisponível.
- **FR-011**: Toda operação MUST dar retorno: mensagem de sucesso ("Gasto lançado.", "Gasto atualizado.", "Gasto excluído.", "Mês criado.", "Mês fechado.", "Mês reaberto.", "Mês excluído.") ou o erro da API.
- **FR-012**: Excluir uma categoria na tela de categorias MUST permitir escolher a categoria que recebe os gastos.
- **FR-013**: A tela MUST funcionar a partir de 360 px de largura, por teclado e com leitor de tela (rótulos e mensagens anunciadas).

### Key Entities

- Usa **Mês de referência** (spec 007), **Gasto**, **Totais do mês** (spec 008) e **Categoria** (spec 006). Nenhuma entidade nova.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Lançar um gasto, do clique no campo descrição até ver a linha na tabela, leva menos de 30 segundos.
- **SC-002**: Em 100% das operações a pessoa vê uma mensagem de sucesso ou de erro.
- **SC-003**: Os totais exibidos são idênticos, ao centavo, aos da API em 100% dos casos (a tela não soma nada).
- **SC-004**: Em 360 px de largura não há rolagem horizontal em nenhuma parte da tela.

## Assumptions

- **Recorrentes e parcelados** entram no formulário nas specs da US-07b e da US-10.
- **"Criar a partir do anterior"** (US-09) entra no seletor na spec da US-09.
- **Data padrão** do formulário: hoje, se cair no mês exibido; senão o dia 1 do mês.
- **Ordenação e filtro** são de exibição e rodam na tela, sobre a lista já carregada do mês; a
  comparação de valores é exata (centavos inteiros), sem ponto flutuante.
- **Sem paginação**: um mês tem dezenas a centenas de gastos.
