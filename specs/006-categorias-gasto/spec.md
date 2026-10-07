# Feature Specification: Categorias de Gasto

**Feature Branch**: `006-categorias-gasto`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "US-05: Como usuário, quero gerenciar categorias de gasto, para organizar meus lançamentos do meu jeito. Critérios: categorias padrão são criadas no cadastro (Moradia, Alimentação, Transporte, Saúde, Lazer, Educação, Outros), e usuários cadastrados antes da US-05 também as recebem; é possível criar, renomear e excluir categorias (nome único por usuário); cada categoria pode ter uma cor para os gráficos; uma categoria com gastos vinculados não pode ser excluída sem escolher outra categoria para receber esses gastos."

## Clarifications

### Session 2026-10-06

- Q: Esta spec entrega também a tela de categorias? → A: Sim. API e uma tela simples de categorias
  (listar, criar, renomear, trocar a cor e excluir), com item novo no menu do layout (spec 005).
- Q: Como entregar a exclusão de categoria com gastos vinculados, se os gastos só existem a partir
  da US-07? → A: Nesta spec a exclusão é livre, porque ainda não existem gastos. A regra de escolher
  uma categoria de destino entra na US-07, junto com os gastos; o critério do backlog fica anotado
  como coberto pela US-07.
- Q: A cor é livre ou escolhida numa paleta? → A: Paleta fixa de 12 cores, pensadas para gráficos
  legíveis e distintos no tema claro e no escuro. Cor fora da paleta é recusada.

## User Scenarios & Testing *(mandatory)*

> **Contexto**: é o primeiro dado financeiro real do sistema e o primeiro a usar a regra comum de
> dono da spec 004: cada pessoa só vê e mexe nas próprias categorias. Os gastos chegam na US-07,
> e cada gasto vai apontar para uma categoria. Esta spec entrega a API e a tela de categorias
> (Clarifications).

### User Story 1 - Começar com categorias prontas (Priority: P1)

Quem cria uma conta já encontra as 7 categorias padrão (Moradia, Alimentação, Transporte, Saúde,
Lazer, Educação e Outros), cada uma com uma cor, e pode começar a lançar gastos sem configurar
nada. Quem já tinha conta antes desta entrega recebe as mesmas categorias.

**Why this priority**: sem categorias não dá para lançar gasto (US-07). É também o critério que
ficou pendente da US-01 (spec 002).

**Independent Test**: criar uma conta nova e listar as categorias: aparecem as 7 padrão, com cor.
Uma conta criada antes desta entrega também passa a ter as 7.

**Acceptance Scenarios**:

1. **Given** uma pessoa sem conta, **When** cria a conta, **Then** passa a ter exatamente as 7 categorias padrão, cada uma com uma cor.
2. **Given** uma conta criada antes desta entrega e sem categorias, **When** a entrega é instalada, **Then** essa conta passa a ter as 7 categorias padrão.
3. **Given** uma conta que já tem categorias, **When** a entrega é instalada de novo ou atualizada, **Then** nenhuma categoria é duplicada.
4. **Given** duas contas, **When** cada uma lista as categorias, **Then** cada uma vê só as suas, mesmo que os nomes sejam iguais (spec 004).

---

### User Story 2 - Criar e renomear categorias (Priority: P1)

A pessoa cria categorias próprias (por exemplo, "Pets" ou "Assinaturas") e renomeia as que
quiser, inclusive as padrão. Dois nomes iguais na mesma conta não são aceitos.

**Why this priority**: é o "do meu jeito" da história: as padrão raramente servem para todo mundo.

**Independent Test**: criar "Pets", renomear "Lazer" para "Lazer e viagens", tentar criar outra
"Pets" (recusada) e outra "pets" (também recusada).

**Acceptance Scenarios**:

1. **Given** uma conta, **When** a pessoa cria "Pets" com uma cor, **Then** "Pets" aparece na lista com essa cor.
2. **Given** a categoria "Lazer", **When** a pessoa a renomeia para "Lazer e viagens", **Then** o novo nome aparece e a cor é mantida.
3. **Given** a categoria "Pets", **When** a pessoa tenta criar "Pets", " pets " ou "PETS", **Then** recebe "Já existe uma categoria com este nome." e nada é criado.
4. **Given** uma categoria sem nome ou com mais de 50 caracteres, **When** a pessoa tenta salvar, **Then** recebe a mensagem do campo e nada é salvo.
5. **Given** que Bia tem "Pets", **When** Ana cria "Pets", **Then** a categoria é criada (nome único vale por conta).

---

### User Story 3 - Escolher a cor de cada categoria (Priority: P2)

Cada categoria tem uma cor da paleta do sistema (12 cores pensadas para gráficos), usada depois
nos gráficos (US-24). A pessoa troca a cor quando quiser.

**Why this priority**: as cores só aparecem de fato nos gráficos (Sprint 5), mas precisam existir
desde já para que cada categoria nasça com uma.

**Independent Test**: trocar a cor de "Saúde" e ver a nova cor na lista; tentar uma cor fora da
paleta e ser recusada.

**Acceptance Scenarios**:

1. **Given** uma categoria criada sem escolher cor, **When** é salva, **Then** recebe automaticamente uma cor da paleta.
2. **Given** a categoria "Saúde", **When** a pessoa escolhe outra cor, **Then** a nova cor é mantida.
3. **Given** uma cor fora da paleta, **When** a pessoa tenta salvar, **Then** recebe "Escolha uma das cores disponíveis." e a cor anterior é mantida.

---

### User Story 4 - Excluir categorias (Priority: P2)

A pessoa exclui categorias que não usa, depois de confirmar. Enquanto não existem gastos (até a
US-07), a exclusão é livre. A US-07 acrescenta a regra de escolher uma categoria de destino para
os gastos vinculados (Clarifications).

**Why this priority**: arrumar a lista é importante, mas raro.

**Independent Test**: excluir uma categoria, confirmar, e ver que ela some da lista; cancelar a
confirmação e ver que ela continua.

**Acceptance Scenarios**:

1. **Given** uma categoria, **When** a pessoa pede para excluir e confirma, **Then** ela some da lista.
2. **Given** uma categoria, **When** a pessoa pede para excluir e cancela, **Then** nada muda.
3. **Given** uma categoria de outra conta, **When** alguém tenta excluí-la, **Then** recebe "não encontrado" e nada muda (spec 004).

---

### User Story 5 - Gerenciar categorias pela tela (Priority: P1)

A pessoa conectada abre "Categorias" no menu e faz tudo pela tela: vê a lista com nome e cor, cria,
renomeia, troca a cor e exclui. Os erros aparecem ao lado do campo, como nas telas de acesso
(spec 005).

**Why this priority**: sem a tela, as categorias só seriam usadas por comandos; com ela, a US-05
fica utilizável no dia a dia (Clarifications).

**Independent Test**: pelo navegador, abrir "Categorias", ver as 7 padrão, criar "Pets" com uma cor,
tentar criar "pets" (erro no campo), renomear "Lazer", trocar a cor de "Saúde" e excluir "Pets".

**Acceptance Scenarios**:

1. **Given** uma pessoa conectada, **When** escolhe "Categorias" no menu, **Then** vê as próprias categorias em ordem alfabética, cada uma com a amostra da cor e o nome.
2. **Given** a tela de categorias, **When** a pessoa cria uma categoria com nome e cor da paleta, **Then** ela aparece na lista na posição alfabética, sem recarregar a página.
3. **Given** um nome repetido ou vazio, **When** a pessoa salva, **Then** vê a mensagem da API ao lado do campo de nome, e o que digitou continua no campo.
4. **Given** uma categoria, **When** a pessoa a edita (nome ou cor) e salva, **Then** a lista mostra o novo nome e a nova cor.
5. **Given** uma categoria, **When** a pessoa escolhe excluir, **Then** o sistema pede confirmação citando o nome, e só exclui se ela confirmar.
6. **Given** a paleta, **When** a pessoa escolhe uma cor, **Then** cada cor tem nome acessível (ex.: "Verde") e pode ser escolhida só pelo teclado.
7. **Given** uma tela de 360 px, **When** a pessoa usa a tela de categorias, **Then** tudo é utilizável sem rolagem horizontal.

---

### Edge Cases

- **Nome com espaços nas pontas**: os espaços são removidos antes de salvar e de comparar.
- **Maiúsculas e minúsculas**: "Pets" e "pets" são o mesmo nome na mesma conta. Acentos contam:
  "Saude" e "Saúde" são nomes diferentes.
- **Renomear para o próprio nome** (inclusive mudando só maiúsculas, como "lazer" → "Lazer"): é
  aceito.
- **Excluir todas as categorias**: permitido. A pessoa pode ficar sem nenhuma e criar outras depois;
  as padrão não voltam sozinhas.
- **Renomear ou excluir uma categoria padrão**: permitido; as padrão são categorias comuns da conta,
  sem tratamento especial depois de criadas.
- **Categoria de outra pessoa**: abrir, renomear, mudar a cor ou excluir pelo identificador responde
  "não encontrado", como qualquer registro de outra conta (spec 004).
- **Ordem da lista**: alfabética, sem diferenciar maiúsculas e minúsculas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Toda conta criada MUST receber, no mesmo momento do cadastro, as 7 categorias padrão: Moradia, Alimentação, Transporte, Saúde, Lazer, Educação e Outros, cada uma com uma cor própria.
- **FR-002**: Contas criadas antes desta entrega e sem nenhuma categoria MUST receber as 7 categorias padrão uma única vez; contas que já têm categorias MUST NOT ser alteradas.
- **FR-003**: A pessoa MUST poder listar as próprias categorias, em ordem alfabética, com nome e cor.
- **FR-004**: A pessoa MUST poder criar categorias com nome (obrigatório, de 1 a 50 caracteres depois de remover os espaços das pontas) e cor (opcional).
- **FR-005**: O nome MUST ser único dentro da conta, sem diferenciar maiúsculas e minúsculas; repetir um nome MUST ser recusado com "Já existe uma categoria com este nome.".
- **FR-006**: A pessoa MUST poder renomear e trocar a cor das próprias categorias, com as mesmas regras de nome e cor da criação.
- **FR-007**: Toda categoria MUST ter uma cor de uma paleta fixa de 12 cores, cada uma com nome em português; sem cor informada, o sistema MUST atribuir uma da paleta automaticamente. Cor fora da paleta MUST ser recusada com "Escolha uma das cores disponíveis.".
- **FR-008**: A pessoa MUST poder excluir as próprias categorias. Enquanto não existem gastos, a exclusão é livre; a regra de escolher uma categoria de destino para os gastos vinculados é da US-07 (Clarifications).
- **FR-009**: Todas as operações MUST seguir a regra de dono da spec 004 (contrato de isolamento): cada pessoa vê e altera só as próprias categorias, e categoria de outra conta é tratada como inexistente.
- **FR-010**: As mensagens de erro MUST estar em português e indicar como corrigir.
- **FR-011**: A interface MUST ter uma tela de categorias, acessível pelo item "Categorias" do menu e só com sessão, para listar, criar, renomear, trocar a cor e excluir, mostrando os erros da API ao lado do campo (padrões da spec 005).
- **FR-012**: A exclusão pela tela MUST pedir confirmação citando o nome da categoria.
- **FR-013**: A paleta da tela MUST ser a mesma da API (a interface não decide quais cores existem; constituição, Princípio V), e cada cor MUST ter nome acessível e ser escolhível só pelo teclado.
- **FR-014**: A tela de categorias MUST funcionar a partir de 360 px de largura, sem rolagem horizontal.

### Key Entities

- **Categoria**: agrupamento de gastos de uma pessoa. Tem nome (único na conta, sem diferenciar
  maiúsculas), cor (para os gráficos) e dono (spec 004). Uma conta tem zero ou mais categorias.
- **Categorias padrão**: o conjunto inicial de 7 categorias, com nomes e cores definidos, dado a
  toda conta uma única vez.
- **Paleta de cores**: as 12 cores aceitas, cada uma com um código e um nome em português.
- **Gasto** (US-07, futuro): vai apontar para uma categoria; a US-07 acrescenta a exclusão com
  destino.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das contas novas e das contas existentes sem categorias passam a ter as 7 categorias padrão, sem duplicatas.
- **SC-002**: Uma pessoa cria uma categoria nova em até 30 segundos.
- **SC-003**: 100% das tentativas de criar ou renomear para um nome já usado na mesma conta são recusadas, e 0% das tentativas com nome usado só por outra conta são recusadas.
- **SC-004**: Pela tela, uma pessoa cria, renomeia, troca a cor e exclui uma categoria, do começo ao fim, em até 2 minutos.
- **SC-005**: 100% das operações sobre categorias de outra conta respondem como "não encontrado" (spec 004).

## Assumptions

- **Cor** (Clarifications): paleta fixa de 12 cores; as cores exatas e os nomes são definidos no
  plano, pensando em contraste no tema claro e no escuro.
- **Cores das padrão**: cada uma das 7 categorias padrão tem uma cor fixa da paleta, diferente das
  outras, definida no plano.
- **Exclusão com gastos** (Clarifications): o critério do backlog "uma categoria com gastos
  vinculados não pode ser excluída sem escolher outra categoria" fica anotado como coberto pela
  US-07, como os critérios de tela da US-02 ficaram com a US-26.
- **Menu**: "Categorias" é o segundo item do menu, depois de "Início".
- **Sem categoria "protegida"**: nenhuma categoria padrão é obrigatória nem fica bloqueada.
- **Sem subcategorias, ícones nem ordenação manual**: fora do escopo; podem virar itens do backlog.
- **Sem limite de quantidade**: uma pessoa pode ter quantas categorias quiser.
- **Orçamento por categoria** é a US-10b, e o peso de cada categoria na renda é a US-19.
