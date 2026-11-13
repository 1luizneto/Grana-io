# Feature Specification: Modo de Uso

**Feature Branch**: `011-modo-de-uso`

**Created**: 2026-11-13

**Status**: Draft

**Input**: User description: "RNF-09: Como usuário, quero um modo de uso separado do modo de desenvolvimento, para usar o sistema no dia a dia com meus dados reais de forma leve e sem expor detalhes técnicos na rede local. Critérios: um comando documentado sobe o sistema no modo de uso, e outro no modo de desenvolvimento; no modo de uso, a interface é servida como build otimizado e a API roda em servidor de aplicação, sem recarga automática; no modo de uso, erros não exibem detalhes técnicos (stack traces, configurações) para nenhum dispositivo da rede; o modo de uso exige chave secreta própria e se recusa a subir com a chave padrão; os dois modos usam o mesmo banco local, e trocar de modo não perde dados; deve estar concluído antes de lançar dados financeiros reais (origem: clarificação da spec 001-infra-docker). Pendências herdadas da spec 001: hosts explícitos no modo de uso, containers sem root, avisos do check --deploy."

## Clarifications

### Session 2026-11-13

> Sessão respondida em modo autônomo (ver `DECISOES-AUTONOMAS.md`, D-011-*).

- Q: Em que endereço o modo de uso fica? → A: No mesmo do modo de desenvolvimento
  (`http://localhost:5173` e o IP da máquina na porta 5173), para os favoritos e os celulares
  continuarem funcionando ao trocar de modo.
- Q: A API fica acessível direto pela rede no modo de uso? → A: Não. Só a interface fica exposta;
  a API é alcançada por ela (`/api`). Menos superfície na rede local.
- Q: O sistema passa a usar HTTPS? → A: Não nesta spec. É uso em rede doméstica; HTTPS exige
  certificado e fica como melhoria futura (anotada). Os avisos do `check --deploy` sobre HTTPS são
  silenciados com justificativa.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subir no modo de uso (Priority: P1)

A pessoa define uma chave secreta própria uma vez e sobe o sistema no modo de uso com um comando.
A interface abre rápida, como versão otimizada, e nada recarrega sozinho.

**Why this priority**: é o modo para os dados reais.

**Independent Test**: com a chave no `.env`, rodar o comando do modo de uso e usar a interface em
`http://localhost:5173`: login, tela do mês, lançamentos.

**Acceptance Scenarios**:

1. **Given** uma chave própria no `.env`, **When** a pessoa roda o comando do modo de uso, **Then** o sistema sobe e a interface funciona em `http://localhost:5173` e pelo IP da máquina.
2. **Given** o modo de uso no ar, **When** a pessoa abre a interface, **Then** ela é servida como arquivos prontos (versão otimizada), sem o servidor de desenvolvimento.
3. **Given** o modo de uso no ar, **When** alguém altera o código, **Then** nada muda até a pessoa subir de novo (sem recarga automática).
4. **Given** o modo de uso, **When** a pessoa tenta abrir a API direto na porta 8000, **Then** não há resposta (a API só é alcançada pela interface).

---

### User Story 2 - Não expor detalhes técnicos (Priority: P1)

Erros e páginas do modo de uso não mostram rastros de pilha, configurações nem versões.

**Why this priority**: os dados reais ficam acessíveis na rede local.

**Independent Test**: provocar um 404 e um erro na API e ver só mensagens genéricas.

**Acceptance Scenarios**:

1. **Given** o modo de uso, **When** alguém abre um endereço inexistente da API, **Then** recebe uma resposta curta, sem a lista de rotas do sistema.
2. **Given** o modo de uso, **When** acontece um erro interno, **Then** a resposta não traz rastro de pilha nem configuração.
3. **Given** o modo de uso, **When** alguém lê os cabeçalhos das respostas, **Then** eles não informam a versão do servidor.
4. **Given** um `Host` estranho no pedido, **When** ele chega ao sistema, **Then** a API não o usa (hosts fixos).

---

### User Story 3 - Chave obrigatória e troca de modo sem perder dados (Priority: P1)

O modo de uso não sobe com a chave padrão, e trocar de modo mantém tudo.

**Why this priority**: a chave padrão é pública no repositório; os dados não podem sumir.

**Independent Test**: tentar subir sem chave (recusado com mensagem clara); subir com chave,
trocar para desenvolvimento e voltar, conferindo os mesmos dados.

**Acceptance Scenarios**:

1. **Given** nenhum `DJANGO_SECRET_KEY` no `.env`, **When** a pessoa roda o comando do modo de uso, **Then** ele se recusa a subir e diz como definir a chave.
2. **Given** dados criados no modo de desenvolvimento, **When** a pessoa sobe o modo de uso, **Then** os mesmos dados aparecem; e vice-versa.
3. **Given** os dois modos, **When** a pessoa alterna entre eles, **Then** usa só os dois comandos documentados, sem reconstruir manualmente nada além do que o comando já faz.

---

### Edge Cases

- **Chave curta ou fraca**: aceita (a pessoa é responsável), mas a documentação dá o comando para
  gerar uma chave forte.
- **Porta 5173 ocupada**: a mesma variável `FRONTEND_PORT` vale para os dois modos.
- **Os dois modos ao mesmo tempo**: não é suportado; subir um substitui o outro (mesmo projeto).
- **Testes**: continuam rodando com `sh testar.sh` no modo de desenvolvimento.
- **Limite de tentativas de login**: continua contando por dispositivo (o servidor web do modo de
  uso repassa o endereço de quem acessa).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: MUST existir um comando documentado para subir o modo de uso e outro para o modo de desenvolvimento.
- **FR-002**: No modo de uso, a interface MUST ser servida como build otimizado por um servidor web, e a API MUST rodar num servidor de aplicação, sem recarga automática nem código montado do computador.
- **FR-003**: No modo de uso, o modo de depuração MUST ficar desligado, e nenhuma resposta MUST trazer rastro de pilha, configuração ou versão de servidor.
- **FR-004**: O modo de uso MUST se recusar a subir sem `DJANGO_SECRET_KEY` própria, com mensagem que diga como defini-la.
- **FR-005**: No modo de uso, a API MUST aceitar só hosts fixos e conhecidos, e só a interface MUST ficar exposta na rede.
- **FR-006**: Os dois modos MUST usar o mesmo banco local; alternar MUST manter todos os dados.
- **FR-007**: No modo de uso, os processos MUST rodar sem privilégios de administrador nos containers.
- **FR-008**: O limite de tentativas de login MUST continuar contando por dispositivo no modo de uso.
- **FR-009**: Os avisos de segurança da verificação de implantação do framework MUST ser resolvidos ou silenciados com justificativa documentada.

### Key Entities

Nenhuma entidade de dados nova.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Subir o modo de uso, com a chave já definida, exige 1 comando.
- **SC-002**: 0 respostas do modo de uso com rastro de pilha, configuração ou versão de servidor nos cenários do quickstart.
- **SC-003**: 100% dos dados presentes antes de trocar de modo continuam presentes depois (contagem de contas, meses e gastos).
- **SC-004**: A interface do modo de uso carrega com menos de 1/3 dos pedidos de arquivo do modo de desenvolvimento.

## Assumptions

- **Rede doméstica, sem HTTPS** nesta spec (Clarifications).
- **Um modo por vez**; ambos com o mesmo nome de projeto e o mesmo volume de dados.
- **Backups** são a US-25.
