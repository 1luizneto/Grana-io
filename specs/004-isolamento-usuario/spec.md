# Feature Specification: Isolamento de Dados por Usuário

**Feature Branch**: `004-isolamento-usuario`

**Created**: 2026-10-05

**Status**: Draft

**Input**: User description: "US-03: Como usuário, quero que meus dados fiquem isolados dos outros usuários, para preservar minha privacidade. Critérios: todo registro (mês, gasto, categoria, cenário) pertence a um usuário; a API só lista e altera registros do usuário autenticado; acessar o ID de um registro de outro usuário retorna 404 (não 403, para não vazar existência); existem testes automatizados cobrindo o isolamento."

## Clarifications

### Session 2026-10-05

- Q: Como esta spec demonstra o isolamento, se ainda não existe nenhum registro de domínio real?
  → A: Com a regra comum de dono e as verificações automáticas, demonstradas por um registro de
  exemplo que existe só nos testes (não vai para o banco de uso nem aparece para a pessoa
  usuária). Os registros reais (categorias, meses, gastos, cenários) ficam para as USs deles.
- Q: Os registros financeiros são identificados por números sequenciais ou por códigos
  aleatórios? → A: Números sequenciais. A proteção é a resposta de "não encontrado" (FR-005); o
  fato de um identificador permitir estimar quantos registros existem no sistema é aceito.

## User Scenarios & Testing *(mandatory)*

> **Contexto**: esta spec chega antes de qualquer dado financeiro. Os tipos de registro citados no
> backlog (mês, gasto, categoria, cenário) só começam a existir na US-05 em diante. Por isso, o
> que ela entrega é a **regra comum de dono** que todos esses registros vão herdar, junto com
> as verificações automáticas que impedem um registro novo de nascer sem isolamento.
> As histórias abaixo são demonstradas com um **registro de exemplo que existe só nos testes**
> (Clarifications); para a pessoa usuária, nada muda até a US-05.

### User Story 1 - Ver só os próprios registros (Priority: P1)

Uma pessoa conectada consulta seus registros (por exemplo, a lista de gastos do mês) e vê
**somente** o que ela mesma criou. Os registros das outras contas do mesmo sistema não aparecem
em listas, buscas, filtros, contagens ou totais.

**Why this priority**: é o núcleo da privacidade. O sistema é usado por mais de uma pessoa da
casa, no mesmo servidor local; uma lista que mistura contas expõe as finanças de todo mundo
(constituição, Princípio II).

**Independent Test**: com duas contas (Ana e Bia), cada uma cria registros; ao listar, cada uma
recebe apenas os seus, e os totais calculados consideram apenas os seus.

**Acceptance Scenarios**:

1. **Given** Ana tem 3 registros e Bia tem 2, **When** Ana lista os registros, **Then** recebe exatamente os 3 dela.
2. **Given** Ana e Bia têm registros, **When** Ana usa filtros ou busca que também combinariam com registros de Bia, **Then** só aparecem resultados de Ana.
3. **Given** Bia tem registros e Ana não tem nenhum, **When** Ana lista, **Then** recebe uma lista vazia, sem erro e sem pista de que existem outros registros no sistema.
4. **Given** Ana e Bia têm registros, **When** Ana consulta um total ou contagem, **Then** o valor considera apenas os registros de Ana.

---

### User Story 2 - Registro de outra pessoa é tratado como inexistente (Priority: P1)

Se uma pessoa tenta abrir, alterar ou excluir um registro que pertence a outra conta, informando
diretamente o identificador dele, o sistema responde **exatamente como se o registro não
existisse**. Nada é revelado, e nada é alterado.

**Why this priority**: identificadores podem ser adivinhados ou copiados. Responder "proibido"
confirmaria que o registro existe; responder "não encontrado" não vaza nada (critério do backlog).

**Independent Test**: Bia cria um registro; Ana tenta ler, alterar e excluir esse registro pelo
identificador. As três tentativas recebem a mesma resposta dada a um identificador que nunca
existiu, e o registro de Bia continua intacto.

**Acceptance Scenarios**:

1. **Given** um registro de Bia, **When** Ana tenta abri-lo pelo identificador, **Then** recebe "não encontrado", com a mesma resposta de um identificador inexistente.
2. **Given** um registro de Bia, **When** Ana tenta alterá-lo, **Then** recebe "não encontrado" e o registro de Bia não muda.
3. **Given** um registro de Bia, **When** Ana tenta excluí-lo, **Then** recebe "não encontrado" e o registro de Bia continua existindo.
4. **Given** um registro de Ana, **When** Ana abre, altera ou exclui esse registro, **Then** a operação funciona normalmente.

---

### User Story 3 - O dono é sempre quem está conectado (Priority: P1)

Quando uma pessoa cria um registro, o sistema define o dono a partir da sessão. Não importa o que
o pedido diga: não dá para criar um registro em nome de outra conta, nem transferir um registro
existente para outra conta.

**Why this priority**: sem essa regra, alguém poderia "plantar" registros na conta de outra
pessoa ou mover os próprios para lá, bagunçando as finanças alheias (constituição, Princípio II).

**Independent Test**: Ana cria um registro informando no pedido que o dono é Bia; o registro
nasce de Ana. Ana tenta alterar o dono de um registro seu para Bia; o dono continua Ana.

**Acceptance Scenarios**:

1. **Given** Ana conectada, **When** cria um registro, **Then** o registro pertence a Ana.
2. **Given** Ana conectada, **When** cria um registro informando outro dono no pedido, **Then** a informação de dono é ignorada e o registro pertence a Ana.
3. **Given** um registro de Ana, **When** Ana tenta trocar o dono para Bia, **Then** o dono continua Ana.
4. **Given** um registro que faz referência a outro registro (por exemplo, um gasto que aponta para uma categoria), **When** Ana aponta para um registro de Bia, **Then** o pedido é recusado como se o registro referenciado não existisse.

---

### User Story 4 - Todo registro novo já nasce isolado (Priority: P2)

Quem desenvolve as próximas funcionalidades (meses, gastos, categorias, cenários) não precisa
lembrar de implementar o isolamento a cada vez: os registros herdam a regra comum de dono, e
verificações automáticas falham se surgir um tipo de registro sem dono ou uma funcionalidade de
dados sem teste de isolamento.

**Why this priority**: o risco real não está nesta spec, e sim na décima funcionalidade que
esquecer o filtro. A proteção estrutural garante que todas as próximas USs nasçam corretas.
É P2 porque não muda o que a pessoa usuária vê hoje.

**Independent Test**: adicionar um tipo de registro de exemplo sem dono faz a suíte de testes
falhar com mensagem que explica o problema; com dono, a suíte passa.

**Acceptance Scenarios**:

1. **Given** um tipo de registro de dados financeiros sem dono, **When** a suíte de testes roda, **Then** ela falha e aponta o tipo sem dono.
2. **Given** um tipo de registro que segue a regra comum de dono, **When** a suíte roda, **Then** ela passa.
3. **Given** a regra comum de dono, **When** uma funcionalidade de dados a usa, **Then** listar, abrir, alterar e excluir já saem filtrados pelo dono, sem código extra.

---

### Edge Cases

- **Sem sessão**: pedidos sem sessão válida continuam recusados como "não autenticado" (spec 003)
  antes de qualquer consulta de dados. O isolamento só se aplica a quem está conectado.
- **Identificador adivinhado**: como os identificadores são sequenciais, alguém pode testar números
  vizinhos aos seus. Todos os que não forem da própria conta respondem "não encontrado" (FR-005),
  e não há como diferenciar "existe, mas é de outra pessoa" de "não existe".
- **Identificador mal formado** (texto no lugar de número, por exemplo): mesma resposta de
  "não encontrado", sem detalhes técnicos.
- **Registro excluído pelo dono**: depois de excluído, ele também responde "não encontrado" para o
  próprio dono, igual ao registro de outra pessoa.
- **Nomes repetidos entre contas**: regras de "nome único" (por exemplo, duas categorias com o
  mesmo nome) valem **dentro de cada conta**. Ana e Bia podem ter, cada uma, uma categoria
  "Mercado"; uma mensagem como "já existe" nunca pode ser causada por um registro de outra conta,
  pois isso revelaria a existência dele.
- **Operações em lote** (excluir ou alterar vários de uma vez, quando existirem): atingem apenas
  os registros do dono. Itens de outra conta são tratados como inexistentes.
- **Conta desativada**: sem sessão, ela não acessa nada (spec 003). Os registros dela continuam
  guardados e invisíveis para as outras contas.
- **Conta removida**: não existe exclusão de conta no backlog atual. Se uma conta for removida
  por manutenção, os registros dela são removidos junto, nunca ficando sem dono nem passando para
  outra conta.
- **Administração**: o sistema não tem painel administrativo, e nenhuma conta enxerga os dados
  das outras pela aplicação.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Todo registro de dados financeiros (mês, gasto, categoria, cenário e os que vierem depois) MUST pertencer a exatamente uma conta, e MUST NOT existir sem dono.
- **FR-002**: O dono de um registro MUST ser definido pelo sistema a partir da sessão no momento da criação; qualquer informação de dono enviada no pedido MUST ser ignorada.
- **FR-003**: O dono de um registro MUST NOT poder ser alterado depois da criação.
- **FR-004**: Listas, buscas, filtros, contagens e totais MUST considerar apenas os registros da conta conectada.
- **FR-005**: Abrir, alterar ou excluir um registro de outra conta MUST produzir a mesma resposta de "não encontrado" dada a um identificador inexistente (mesmo código e mesma mensagem), e MUST NOT alterar o registro.
- **FR-006**: Um registro que referencia outro registro MUST só poder apontar para registros da mesma conta; apontar para registro de outra conta MUST ser recusado como se o registro referenciado não existisse.
- **FR-007**: Regras de unicidade de registros de dados financeiros MUST valer dentro de cada conta, nunca entre contas.
- **FR-008**: A filtragem por dono MUST acontecer antes de qualquer outra operação sobre os dados (busca, validação, alteração ou exclusão).
- **FR-009**: Os registros de dados financeiros MUST seguir uma regra comum de dono, compartilhada por todos, em vez de cada funcionalidade implementar o isolamento por conta própria.
- **FR-010**: O sistema MUST ter verificações automáticas que falhem quando surgir um tipo de registro de dados financeiros sem dono.
- **FR-011**: Toda funcionalidade de dados financeiros MUST ter testes automatizados cobrindo, no mínimo: listar, abrir, alterar e excluir com uma segunda conta, e a tentativa de definir outro dono.
- **FR-012**: Os registros de uma conta removida MUST ser removidos junto com ela.
- **FR-013**: Os comportamentos FR-002 a FR-008 MUST ser demonstrados nesta spec por testes automatizados com um registro de exemplo que existe só nos testes, exercitado por duas contas; esse registro MUST NOT existir no banco de uso nem ficar acessível pela aplicação.

### Key Entities

- **Registro com dono**: a regra comum de todos os dados financeiros. Todo registro tem um dono
  (a conta que o criou), definido pelo sistema e imutável. Mês, gasto, categoria e cenário são
  registros com dono a partir das próximas USs.
- **Usuário** (spec 002): passa a ser o dono dos registros. Uma conta tem zero ou mais
  registros; cada registro tem exatamente uma conta.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em 100% dos cenários de teste com duas contas, nenhuma lista, busca, contagem ou total devolve dado de outra conta.
- **SC-002**: Em 100% das tentativas de abrir, alterar ou excluir registro de outra conta, a resposta é idêntica à de um identificador inexistente, e o registro fica intacto.
- **SC-003**: Em 100% das tentativas de criar ou transferir registro em nome de outra conta, o registro fica com quem está conectado.
- **SC-004**: Um tipo de registro de dados financeiros sem dono é detectado pela suíte de testes antes do merge em 100% dos casos.
- **SC-005**: As próximas USs de dados (a partir da US-05) conseguem ter isolamento completo apenas seguindo a regra comum, sem escrever filtro por dono à mão.

## Assumptions

- **Escopo só da API e das regras**: não há tela nesta spec. A interface (US-26 em diante) só
  exibe o que a API devolve, então o isolamento feito na API vale para ela também
  (constituição, Princípio V).
- **Sem registros de domínio próprios**: mês, gasto, categoria e cenário são criados nas USs
  deles (US-05, US-06, US-07, US-11...). Cada uma deve seguir a regra comum desta spec e trazer
  os próprios testes de isolamento (FR-011). Até lá, o isolamento é provado pelo registro de
  exemplo dos testes (FR-013).
- **Critérios do backlog**: "todo registro pertence a um usuário", "a API só lista e altera
  registros do usuário autenticado" e "acessar ID de outro usuário retorna 404" ficam cobertos
  pela regra comum e pelos testes com o registro de exemplo; cada US de dados confirma o mesmo
  para o seu registro real.
- **Dados da própria conta**: a consulta e a futura alteração da conta (spec 003, US-04) já são
  da pessoa conectada por definição e não são "registros com dono".
- **Identificadores** (Clarifications): os registros usam números sequenciais. A resposta de "não
  encontrado" para registros de outras contas (FR-005) é a proteção adotada. Pelo número de um
  registro próprio, dá para estimar quantos registros existem no sistema inteiro; esse vazamento
  de contagem é aceito por ser um sistema local, de poucas pessoas da mesma casa, e não revela
  conteúdo de ninguém.
- **Sem compartilhamento**: não existe registro compartilhado entre contas (por exemplo, finanças
  de casal). Se surgir essa necessidade, ela vira um item novo do backlog.
- **Sem administração**: não existe conta capaz de ver os dados das outras pela aplicação.
  Acesso direto ao banco local, por quem administra o computador, está fora do escopo.
