# Feature Specification: Lançar, Editar e Excluir Gastos

**Feature Branch**: `008-lancar-gastos`

**Created**: 2026-11-13

**Status**: Draft

**Input**: User description: "US-07 e US-08. US-07: Como usuário, quero lançar gastos no mês por categoria, para saber para onde meu dinheiro vai. Critérios: um gasto tem descrição, valor, categoria, data e forma de pagamento (opcional: dinheiro, débito, crédito, Pix); valores zerados, negativos ou não numéricos são bloqueados; a data precisa estar dentro do mês de referência; o gasto é persistido e o total do mês e da categoria é atualizado; excluir uma categoria com gastos vinculados exige escolher outra categoria para receber esses gastos (herdado da US-05); um mês fechado não aceita novos gastos até ser reaberto (herdado da US-06); um mês com gastos não pode ser excluído (herdado da US-06). US-08: Como usuário, quero editar e excluir gastos, para corrigir lançamentos errados. Critérios: é possível alterar todos os campos de um gasto; as validações da US-07 valem também na edição; há confirmação antes de excluir; meses fechados bloqueiam edição e exclusão até serem reabertos."

## Clarifications

### Session 2026-11-13

> Sessão respondida em modo autônomo (ver `DECISOES-AUTONOMAS.md`, D-008-*).

- Q: A US-07 e a US-08 entram na mesma spec? → A: Sim. O kit de isolamento da spec 004 exige
  abrir, alterar e excluir todo registro novo, e a regra do mês fechado vale para as três
  operações; separar duplicaria quase toda a spec. A confirmação antes de excluir é de tela e fica
  com a US-27.
- Q: Ao excluir uma categoria com gastos, os gastos que estão em meses fechados também são
  movidos? → A: Sim. Mover de categoria não muda o total do mês; exigir reabrir cada mês fechado
  tornaria a exclusão impraticável. A pessoa escolhe o destino de forma explícita.
- Q: Como a API recebe valores com mais de 2 casas decimais (ex.: 10,555)? → A: Recusa, com
  "Use no máximo 2 casas decimais.". Arredondar em silêncio mudaria o valor digitado.
- Q: O valor aceita vírgula ("12,50")? → A: Não na API, que segue o padrão numérico (ponto). A
  tela (US-27) aceita a vírgula e converte antes de enviar.

## User Scenarios & Testing *(mandatory)*

> **Contexto**: o gasto é o dado central do EP-02. Pertence a um mês de referência (spec 007) e a
> uma categoria (spec 006), da mesma pessoa (spec 004). Esta spec entrega a API; a tela do mês, com
> o formulário rápido e a confirmação antes de excluir, é a US-27.

### User Story 1 - Lançar um gasto (Priority: P1)

A pessoa registra um gasto num mês aberto: descrição, valor, categoria, data e, se quiser, a forma
de pagamento.

**Why this priority**: é o motivo de o sistema existir; sem gastos não há totais nem comparação.

**Independent Test**: com o mês 10/2026 aberto, lançar "Mercado", 150,30, Alimentação, 05/10/2026,
Pix, e vê-lo gravado; tentar valor 0 e data 05/11/2026 e ser recusado.

**Acceptance Scenarios**:

1. **Given** o mês 10/2026 aberto e a categoria Alimentação, **When** a pessoa lança "Mercado", 150,30, em 05/10/2026, pago com Pix, **Then** o gasto é gravado com esses dados.
2. **Given** o mesmo mês, **When** a pessoa lança sem forma de pagamento, **Then** o gasto é gravado sem ela.
3. **Given** valor 0, negativo ou texto, **When** a pessoa tenta lançar, **Then** recebe a mensagem do campo valor e nada é gravado.
4. **Given** o mês 10/2026, **When** a data é 05/11/2026, **Then** recebe "A data precisa estar dentro de 10/2026." e nada é gravado.
5. **Given** o mês 10/2026 fechado, **When** a pessoa tenta lançar, **Then** recebe "O mês 10/2026 está fechado. Reabra o mês para alterar os gastos." e nada é gravado.
6. **Given** uma categoria ou um mês de outra conta, **When** a pessoa tenta usá-los, **Then** recebe "Registro não encontrado." no campo (spec 004).

---

### User Story 2 - Ver os gastos e os totais do mês (Priority: P1)

A pessoa vê os gastos de um mês, do mais antigo para o mais recente, e os totais: o do mês e o de
cada categoria.

**Why this priority**: "saber para onde o dinheiro vai" é o valor da US-07; os totais são a resposta.

**Independent Test**: lançar 3 gastos em 2 categorias e conferir a lista e os totais, ao centavo.

**Acceptance Scenarios**:

1. **Given** gastos em 10/2026 e em 11/2026, **When** a pessoa lista os gastos de 10/2026, **Then** vê só os de 10/2026, por data (e, na mesma data, na ordem de lançamento).
2. **Given** Mercado 150,30 e Feira 49,70 (Alimentação) e Uber 23,45 (Transporte) em 10/2026, **When** a pessoa pede os totais do mês, **Then** vê total 223,45, Alimentação 200,00 e Transporte 23,45.
3. **Given** um mês sem gastos, **When** a pessoa pede os totais, **Then** vê total 0,00 e nenhuma categoria.
4. **Given** um gasto novo, editado ou excluído, **When** a pessoa pede os totais de novo, **Then** eles já refletem a mudança.

---

### User Story 3 - Corrigir e excluir um gasto (Priority: P2)

A pessoa altera qualquer campo de um gasto ou o exclui, com as mesmas validações do lançamento.

**Why this priority**: erros de digitação acontecem; sem correção os totais ficam errados.

**Independent Test**: lançar com valor errado, corrigir o valor e a categoria, conferir os totais;
excluir e conferir que sumiu.

**Acceptance Scenarios**:

1. **Given** um gasto em mês aberto, **When** a pessoa muda descrição, valor, categoria, data ou forma de pagamento, **Then** a mudança é gravada.
2. **Given** um gasto, **When** a pessoa tenta valor 0 ou data fora do mês, **Then** recebe a mesma mensagem do lançamento e nada muda.
3. **Given** um gasto em 10/2026 (aberto), **When** a pessoa o move para 11/2026 (aberto) com uma data de novembro, **Then** ele passa a contar em 11/2026.
4. **Given** um gasto em mês aberto, **When** a pessoa o exclui, **Then** ele some da lista e dos totais.
5. **Given** um gasto em mês fechado, **When** a pessoa tenta alterá-lo ou excluí-lo, **Then** recebe a mensagem de mês fechado e nada muda; o mesmo vale para mover um gasto para um mês fechado.

---

### User Story 4 - Proteger o histórico ao excluir mês ou categoria (Priority: P2)

Excluir um mês ou uma categoria não pode apagar nem deixar gastos "órfãos".

**Why this priority**: critérios herdados das US-05 e US-06; sem eles a exclusão perde dados.

**Independent Test**: tentar excluir um mês com gastos (recusado); excluir uma categoria com gastos
escolhendo outra para recebê-los e ver os gastos na categoria nova.

**Acceptance Scenarios**:

1. **Given** o mês 10/2026 com gastos, **When** a pessoa tenta excluí-lo, **Then** recebe "Exclua ou mova os gastos antes de excluir o mês." e nada muda.
2. **Given** a categoria Lazer com gastos, **When** a pessoa tenta excluí-la sem dizer para onde vão os gastos, **Then** recebe "Esta categoria tem gastos. Escolha outra categoria para recebê-los." e nada muda.
3. **Given** a categoria Lazer com gastos, **When** a pessoa a exclui escolhendo Outros como destino, **Then** os gastos passam para Outros e Lazer deixa de existir.
4. **Given** um destino inválido (a própria categoria, inexistente ou de outra conta), **When** a pessoa tenta excluir, **Then** recebe "Escolha outra categoria sua para receber os gastos." e nada muda.
5. **Given** uma categoria sem gastos, **When** a pessoa a exclui, **Then** ela é excluída como antes (spec 006).

---

### Edge Cases

- **Valor com mais de 2 casas** (10,555): recusado com "Use no máximo 2 casas decimais.".
- **Valor muito alto** (acima de 9.999.999.999,99): recusado com mensagem de limite.
- **Descrição só com espaços**: tratada como vazia ("Este campo é obrigatório.").
- **Último dia do mês**: 31/10/2026 é aceito em 10/2026; 29/02 só em ano bissexto.
- **Data inválida** (31/09, texto): recusada no campo data.
- **Mover gasto de mês**: as regras de data e de mês fechado valem para o mês de destino e para o
  de origem.
- **Mês fechado depois do lançamento**: os gastos continuam visíveis e entram nos totais.
- **Gastos de outra pessoa**: abrir, alterar ou excluir responde "não encontrado" (spec 004).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A pessoa MUST poder lançar um gasto com descrição (até 100 caracteres), valor, categoria, data, mês de referência e, opcionalmente, forma de pagamento (dinheiro, débito, crédito ou Pix).
- **FR-002**: O valor MUST ser maior que zero, ter no máximo 2 casas decimais e no máximo 9.999.999.999,99; valores zerados, negativos ou não numéricos MUST ser recusados com mensagem no campo.
- **FR-003**: A data MUST estar dentro do mês de referência do gasto; fora dele, MUST ser recusada com "A data precisa estar dentro de MM/AAAA.".
- **FR-004**: Categoria e mês MUST ser da própria pessoa; de outra conta, MUST ser tratados como inexistentes ("Registro não encontrado.").
- **FR-005**: A pessoa MUST poder listar os gastos de um mês, em ordem de data e, na mesma data, de lançamento.
- **FR-006**: A pessoa MUST poder consultar o total do mês e o total de cada categoria com gastos no mês, calculados no sistema com precisão de centavos e sempre atualizados.
- **FR-007**: A pessoa MUST poder alterar todos os campos de um gasto, com as mesmas validações do lançamento, e excluí-lo.
- **FR-008**: Em mês fechado, lançar, alterar e excluir gastos MUST ser recusado com "O mês MM/AAAA está fechado. Reabra o mês para alterar os gastos."; mover um gasto para ou de um mês fechado também.
- **FR-009**: Um mês com gastos MUST NOT poder ser excluído ("Exclua ou mova os gastos antes de excluir o mês.").
- **FR-010**: Excluir uma categoria com gastos MUST exigir uma categoria de destino da própria pessoa, diferente da excluída; os gastos MUST passar para o destino antes da exclusão, de uma vez (tudo ou nada).
- **FR-011**: Valores monetários MUST ser guardados e calculados como decimais exatos, nunca como ponto flutuante, com a regra de arredondamento única documentada (RNF-03).
- **FR-012**: Todas as operações MUST seguir a regra de dono da spec 004.
- **FR-013**: As mensagens de erro MUST estar em português e indicar como corrigir.

### Key Entities

- **Gasto**: descrição, valor, data, forma de pagamento (opcional), mês de referência, categoria e
  dono. Conta no total do mês e da categoria.
- **Mês de referência** (spec 007): agrupa os gastos; o estado "fechado" bloqueia mudanças neles.
- **Categoria** (spec 006): classifica os gastos; ao ser excluída, entrega os gastos a outra.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das tentativas com valor zerado, negativo, não numérico ou com mais de 2 casas são recusadas.
- **SC-002**: 100% dos gastos com data fora do mês de referência são recusados.
- **SC-003**: Os totais do mês e por categoria batem ao centavo com a soma manual dos gastos em 100% dos casos de teste, inclusive com valores como 0,10 + 0,20.
- **SC-004**: 100% das tentativas de lançar, alterar ou excluir gastos em mês fechado são recusadas.
- **SC-005**: Nenhum gasto é perdido ao excluir categoria ou mês: 0 gastos órfãos em todos os casos de teste.
- **SC-006**: 100% das operações sobre gastos de outra conta respondem como "não encontrado".

## Assumptions

- **Só API nesta spec**: a tela (lista, formulário rápido, confirmação antes de excluir e a escolha
  do destino ao excluir categoria na tela de categorias) é da US-27 / próxima spec.
- **Recorrentes (US-07b) e parcelados (US-10)** não entram; o gasto desta spec é avulso.
- **Ponto decimal na API**; a tela converte a vírgula.
- **Moeda única**: reais. Não há conversão de moeda.
- **Sem limite de gastos por mês**; o volume esperado é de dezenas a poucas centenas por mês.
