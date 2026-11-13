# Feature Specification: Gastos Fixos

**Feature Branch**: `010-gastos-fixos`

**Created**: 2026-11-13

**Status**: Draft

**Input**: User description: "US-07b: Como usuário, quero cadastrar gastos fixos (aluguel, internet, assinaturas), para não precisar lançá-los todo mês. Critérios: é possível marcar um gasto como recorrente, com dia de vencimento; ao criar um novo mês, os gastos recorrentes ativos são gerados automaticamente; um gasto recorrente pode ter data de fim ou ser desativado; alterar o valor do recorrente afeta só os meses seguintes, nunca os já existentes."

## Clarifications

### Session 2026-11-13

> Sessão respondida em modo autônomo (ver `DECISOES-AUTONOMAS.md`, D-010-*).

- Q: Como a pessoa "marca um gasto como recorrente"? → A: De dois jeitos: no formulário de gasto
  da tela do mês, a opção "Repetir todo mês" transforma o lançamento em gasto fixo (o dia de
  vencimento é o dia da data); e numa tela própria, "Gastos fixos", onde a pessoa cria, altera,
  encerra, desativa e exclui os fixos.
- Q: Os gastos fixos são gerados também em meses que já existem? → A: Não. Só ao criar um mês
  novo. Meses existentes nunca mudam por causa de um fixo (critério 4).
- Q: E se o dia de vencimento não existir no mês (dia 31 em novembro)? → A: Usa o último dia do
  mês.
- Q: Excluir um gasto fixo apaga os gastos já gerados? → A: Não; eles ficam como gastos comuns.

## User Scenarios & Testing *(mandatory)*

> **Contexto**: gasto fixo é um modelo que gera um gasto (spec 008) em cada mês novo (spec 007).
> Segue a regra de dono (spec 004). Valores em `Decimal` (RNF-03).

### User Story 1 - Cadastrar um gasto fixo (Priority: P1)

A pessoa cadastra "Aluguel", R$ 1.500,00, Moradia, vencimento dia 5, a partir de 11/2026.

**Why this priority**: sem o cadastro não há o que gerar.

**Independent Test**: criar o fixo e vê-lo na lista de gastos fixos, ativo.

**Acceptance Scenarios**:

1. **Given** a tela "Gastos fixos", **When** a pessoa cadastra descrição, valor, categoria, forma (opcional), dia de vencimento (1 a 31) e mês de início, **Then** o fixo aparece na lista, ativo, sem mês de fim.
2. **Given** dia 0 ou 32, valor zero, categoria de outra conta ou fim antes do início, **When** tenta salvar, **Then** recebe a mensagem do campo.
3. **Given** o formulário de gasto da tela do mês, **When** a pessoa lança "Internet", R$ 99,90, dia 10/11/2026, com "Repetir todo mês", **Then** o gasto é lançado em 11/2026 e um fixo "Internet" com vencimento dia 10, a partir de 11/2026, é criado.

---

### User Story 2 - Gerar os fixos ao criar um mês (Priority: P1)

Ao criar um mês, os fixos ativos daquele período viram gastos do mês.

**Why this priority**: é o "não precisar lançar todo mês".

**Independent Test**: com Aluguel (dia 5, desde 11/2026) e Internet (dia 31, desde 11/2026), criar
12/2026 e ver 05/12 Aluguel e 31/12 Internet; criar 02/2027 e ver Internet em 28/02.

**Acceptance Scenarios**:

1. **Given** fixos ativos que começam até o mês criado e terminam depois dele (ou não terminam), **When** a pessoa cria o mês, **Then** cada um vira um gasto do mês com a descrição, o valor, a categoria, a forma e a data do vencimento.
2. **Given** vencimento dia 31, **When** o mês tem 30 dias (ou fevereiro), **Then** a data é o último dia do mês.
3. **Given** um fixo desativado, que ainda não começou ou que já terminou, **When** o mês é criado, **Then** ele não é gerado.
4. **Given** um mês já existente, **When** um fixo é criado ou alterado, **Then** os gastos desse mês não mudam.
5. **Given** fixos de outra pessoa, **When** Ana cria um mês, **Then** só os fixos dela são gerados.

---

### User Story 3 - Alterar, encerrar, desativar e excluir (Priority: P2)

A pessoa reajusta o aluguel, encerra uma assinatura, pausa um fixo e exclui um cadastrado errado.

**Why this priority**: os fixos mudam com o tempo.

**Independent Test**: mudar o valor do aluguel e ver que só o mês criado depois usa o valor novo.

**Acceptance Scenarios**:

1. **Given** Aluguel R$ 1.500,00 e o mês 12/2026 já gerado, **When** a pessoa muda o valor para R$ 1.600,00, **Then** 12/2026 continua com R$ 1.500,00 e 01/2027, criado depois, vem com R$ 1.600,00.
2. **Given** um fixo, **When** a pessoa define o mês de fim 01/2027, **Then** 02/2027 não o recebe.
3. **Given** um fixo, **When** a pessoa o desativa, **Then** os meses criados depois não o recebem; reativando, voltam a receber.
4. **Given** um fixo, **When** a pessoa o exclui (com confirmação), **Then** ele some da lista e os gastos já gerados continuam nos meses.

---

### Edge Cases

- **Categoria do fixo excluída**: ao excluir uma categoria (spec 008), os fixos dela também passam
  para a categoria escolhida; uma categoria só com fixos também exige o destino.
- **Mês de início no futuro**: aceito; o fixo só gera a partir dele.
- **Fim igual ao início**: aceito (gera só naquele mês).
- **Gasto gerado**: é um gasto comum; pode ser editado ou excluído no mês, sem mudar o fixo.
- **"Repetir todo mês" num mês fechado**: recusado como qualquer lançamento (spec 008).
- **Fixos de outra pessoa**: abrir, alterar ou excluir responde "não encontrado".

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A pessoa MUST poder cadastrar gastos fixos com descrição, valor, categoria, forma de pagamento (opcional), dia de vencimento (1 a 31), mês de início e mês de fim (opcional), com as validações de descrição, valor e categoria da spec 008.
- **FR-002**: O mês de fim, quando informado, MUST ser igual ou posterior ao de início ("O mês de fim precisa ser igual ou posterior ao de início.").
- **FR-003**: Lançar um gasto com "Repetir todo mês" MUST lançar o gasto e criar o fixo correspondente (vencimento = dia da data; início = mês do gasto), tudo ou nada.
- **FR-004**: Criar um mês MUST gerar, de uma vez com o mês, um gasto para cada fixo ativo da pessoa cujo período inclua o mês, na data do vencimento (ou no último dia do mês, se o dia não existir).
- **FR-005**: Fixos MUST NOT alterar meses já existentes: criar, alterar, encerrar, desativar ou excluir um fixo só afeta meses criados depois.
- **FR-006**: A pessoa MUST poder listar, alterar, desativar, reativar e excluir os próprios fixos; excluir MUST manter os gastos já gerados.
- **FR-007**: Gastos gerados MUST indicar de qual fixo vieram (para a tela e para a US-09 não duplicá-los).
- **FR-008**: Excluir uma categoria MUST levar também os fixos dela para a categoria de destino.
- **FR-009**: A tela "Gastos fixos" MUST ficar no menu e seguir os padrões de tela (erros da API, retorno de sucesso, confirmação ao excluir, 360 px, teclado).
- **FR-010**: Todas as operações MUST seguir a regra de dono da spec 004.

### Key Entities

- **Gasto fixo**: descrição, valor, categoria, forma de pagamento, dia de vencimento, mês de
  início, mês de fim (opcional), ativo e dono. Modelo para gerar gastos.
- **Gasto** (spec 008): ganha a referência opcional ao fixo de origem.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos meses criados, cada fixo ativo do período gera exatamente um gasto, e nenhum fixo fora do período gera.
- **SC-002**: 0 alterações em gastos de meses existentes ao mexer em fixos.
- **SC-003**: Cadastrar um fixo pela tela leva menos de 1 minuto.
- **SC-004**: 100% das operações sobre fixos de outra conta respondem "não encontrado".

## Assumptions

- **Geração só na criação do mês** (pela tela ou pela API). Não há tarefa agendada.
- **Copiar do mês anterior** (US-09) e **parcelados** (US-10) ficam para as specs deles; a US-09
  vai usar a referência ao fixo para não duplicar.
- **Mês de início e de fim** são meses (MM/AAAA), não datas.
