# Feature Specification: Mês de Referência

**Feature Branch**: `007-mes-referencia`

**Created**: 2026-10-07

**Status**: Draft

**Input**: User description: "US-06: Como usuário, quero criar um mês de referência (MM/AAAA), para agrupar os gastos daquele período. Critérios: é possível criar um mês informando mês e ano; cada mês existe uma única vez por usuário, e duplicados são rejeitados com mensagem clara; os meses aparecem listados em ordem cronológica; um mês pode ser marcado como 'fechado', o que bloqueia edições acidentais."

## Clarifications

### Session 2026-10-07

- Q: Um mês pode ser excluído? Se sim, o que acontece quando ele já tiver gastos? → A: Pode, se
  estiver aberto. A partir da US-07, só se não tiver gastos ("Exclua ou mova os gastos antes de
  excluir o mês."); essa regra entra na US-07, junto com os gastos, como aconteceu com as
  categorias (spec 006).

## User Scenarios & Testing *(mandatory)*

> **Contexto**: o mês de referência é a "pasta" onde os gastos da US-07 vão ficar. É o segundo
> dado financeiro, e segue a regra de dono da spec 004: cada pessoa só vê e mexe nos próprios
> meses. A tela do mês, com o seletor que cria meses, é da US-27; esta spec entrega a API.

### User Story 1 - Criar um mês (Priority: P1)

A pessoa cria o mês em que quer lançar gastos, informando mês e ano (ex.: 10/2026). Cada mês
existe uma única vez na conta.

**Why this priority**: sem mês não há onde lançar gastos (US-07).

**Independent Test**: criar 10/2026; tentar criar 10/2026 de novo e ser recusado; criar o mesmo
mês em outra conta e ser aceito.

**Acceptance Scenarios**:

1. **Given** uma conta sem meses, **When** a pessoa cria o mês 10 de 2026, **Then** o mês 10/2026 passa a existir, aberto.
2. **Given** que 10/2026 já existe na conta, **When** a pessoa tenta criá-lo de novo, **Then** recebe "Este mês já foi criado." e nada é criado.
3. **Given** que Bia já tem 10/2026, **When** Ana cria 10/2026, **Then** o mês de Ana é criado (a regra de mês único vale por conta).
4. **Given** mês 13, mês 0, ano 1999 ou ano 2101, **When** a pessoa tenta criar, **Then** recebe a mensagem do campo correspondente e nada é criado.
5. **Given** mês ou ano faltando, **When** a pessoa tenta criar, **Then** recebe "Este campo é obrigatório." no campo que faltou.

---

### User Story 2 - Ver os meses em ordem cronológica (Priority: P1)

A pessoa vê os próprios meses do mais antigo para o mais recente, cada um como MM/AAAA e com a
indicação de aberto ou fechado.

**Why this priority**: é como a pessoa encontra o mês em que vai trabalhar (a US-27 usa essa lista
no seletor).

**Independent Test**: criar 03/2027, 12/2026 e 01/2026 nessa ordem e ver a lista 01/2026, 12/2026,
03/2027.

**Acceptance Scenarios**:

1. **Given** os meses 03/2027, 12/2026 e 01/2026 criados nessa ordem, **When** a pessoa lista os meses, **Then** vê 01/2026, 12/2026, 03/2027.
2. **Given** uma conta sem meses, **When** a pessoa lista, **Then** recebe uma lista vazia.
3. **Given** meses de Ana e de Bia, **When** Ana lista, **Then** vê só os dela (spec 004).

---

### User Story 3 - Fechar e reabrir um mês (Priority: P2)

Quando termina de revisar um mês, a pessoa o marca como "fechado" para não alterá-lo por acidente.
Se precisar corrigir algo, reabre.

**Why this priority**: protege o histórico, mas só faz diferença quando houver gastos (US-07 e
US-08 bloqueiam lançar, editar e excluir gastos em mês fechado).

**Independent Test**: fechar 10/2026, ver o mês como fechado, tentar excluí-lo (recusado), reabrir
e ver o mês aberto de novo.

**Acceptance Scenarios**:

1. **Given** o mês 10/2026 aberto, **When** a pessoa o fecha, **Then** ele aparece como fechado.
2. **Given** o mês 10/2026 fechado, **When** a pessoa o reabre, **Then** ele aparece como aberto.
3. **Given** o mês 10/2026 fechado, **When** a pessoa tenta excluí-lo, **Then** recebe "Reabra o mês antes de excluí-lo." e nada muda.
4. **Given** o mês 10/2026 fechado, **When** a pessoa tenta trocar o mês ou o ano dele, **Then** a alteração é recusada (ver FR-006).

---

### User Story 4 - Excluir um mês (Priority: P3)

A pessoa exclui um mês criado por engano, depois de confirmar.

**Why this priority**: arrumação rara; o essencial é criar e listar.

**Independent Test**: criar 11/2026 por engano, excluir e ver que sumiu.

**Acceptance Scenarios**:

1. **Given** o mês 11/2026 aberto, **When** a pessoa o exclui, **Then** ele some da lista.
2. **Given** o mês 11/2026 fechado, **When** a pessoa tenta excluí-lo, **Then** recebe "Reabra o mês antes de excluí-lo." e ele continua na lista.
3. **Given** um mês de outra conta, **When** alguém tenta excluí-lo, **Then** recebe "não encontrado" e nada muda.

---

### Edge Cases

- **Mês e ano como texto** ("10", "2026"): aceitos se forem números inteiros válidos; "outubro" ou
  "10.5" são recusados no campo.
- **Meses futuros e passados**: permitidos dentro de 2000 a 2100 (planejar o ano seguinte ou lançar
  um mês antigo).
- **Mês de outra pessoa**: abrir, fechar, reabrir ou excluir pelo identificador responde "não
  encontrado" (spec 004).
- **Dois pedidos iguais ao mesmo tempo**: só um mês é criado; o outro recebe a mensagem de mês
  repetido.
- **Fechar um mês já fechado / reabrir um já aberto**: aceito, sem erro (o estado final é o pedido).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A pessoa MUST poder criar um mês informando mês (1 a 12) e ano (2000 a 2100); o mês nasce aberto.
- **FR-002**: Cada combinação de mês e ano MUST existir uma única vez por conta; repetir MUST ser recusado com "Este mês já foi criado.".
- **FR-003**: A pessoa MUST poder listar os próprios meses em ordem cronológica (do mais antigo para o mais recente), cada um com mês, ano, a forma MM/AAAA e se está fechado.
- **FR-004**: A pessoa MUST poder fechar e reabrir os próprios meses.
- **FR-005**: Um mês fechado MUST NOT poder ser excluído; a recusa MUST dizer "Reabra o mês antes de excluí-lo.".
- **FR-006**: O mês e o ano de um mês já criado MUST NOT poder ser alterados (corrigir é excluir e criar de novo); a única alteração possível é fechar ou reabrir.
- **FR-007**: O estado "fechado" MUST ficar disponível para as próximas USs bloquearem lançamentos e alterações de gastos naquele mês (US-07, US-08).
- **FR-008**: Todas as operações MUST seguir a regra de dono da spec 004: cada pessoa vê e altera só os próprios meses, e mês de outra conta é tratado como inexistente.
- **FR-009**: As mensagens de erro MUST estar em português e indicar como corrigir (ex.: "Informe um mês de 1 a 12.", "Informe um ano de 2000 a 2100.").
- **FR-010**: A pessoa MUST poder excluir os próprios meses abertos. A partir da US-07, um mês com gastos MUST NOT poder ser excluído ("Exclua ou mova os gastos antes de excluir o mês."); essa regra é implementada na US-07 (Clarifications).

### Key Entities

- **Mês de referência**: período de um mês de uma pessoa. Tem mês (1 a 12), ano (2000 a 2100),
  situação (aberto ou fechado) e dono (spec 004). Mês e ano formam a identidade dentro da conta.
- **Gasto** (US-07, futuro): vai pertencer a um mês de referência; é por ele que o fechamento faz
  diferença.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das tentativas de criar um mês já existente na mesma conta são recusadas, e 0% das tentativas com mês existente só em outra conta são recusadas.
- **SC-002**: Em 100% das listagens, os meses aparecem em ordem cronológica, inclusive atravessando anos (12/2026 antes de 01/2027).
- **SC-003**: 100% das tentativas de excluir um mês fechado são recusadas, e o mês continua existindo.
- **SC-004**: 100% das operações sobre meses de outra conta respondem como "não encontrado" (spec 004).

## Assumptions

- **Só API nesta spec**: a tela do mês (com o seletor que cria meses) é a US-27, que já está no
  backlog da Sprint 2; até lá, os meses são usados pela API.
- **Criar a partir do anterior** (copiar gastos) é a US-09; **gastos recorrentes** gerados ao criar
  o mês são a US-07b.
- **Sem criação automática**: o sistema não cria o mês atual sozinho; a pessoa (ou a US-27) cria.
- **Ordem cronológica crescente**, como diz o backlog; a tela da US-27 pode exibir na ordem que
  preferir.
- **Exclusão com gastos** (Clarifications): bloqueada a partir da US-07; o critério fica anotado na
  US-07 do backlog, como o da exclusão de categorias.
- **Faixa de anos** 2000 a 2100: cobre histórico e planejamento sem aceitar erros de digitação
  (ex.: 20026).
