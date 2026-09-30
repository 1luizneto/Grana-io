# Feature Specification: Execução Local com Um Comando (Infraestrutura Docker)

**Feature Branch**: `001-infra-docker`

**Created**: 2026-09-25

**Status**: Draft

**Input**: User description: "RNF-01: Execução local com um comando (Docker) — Como desenvolvedor, quero subir o sistema inteiro com um comando, para rodar localmente sem configuração manual. Critérios do backlog: `docker compose up` sobe banco (PostgreSQL), backend (Django) e frontend (React); os dados do banco persistem em volume entre reinicializações; as migrations rodam automaticamente na subida; variáveis sensíveis ficam num `.env` (com `.env.example` versionado); o README documenta como subir, parar e acessar o sistema. Inclui a parte de infraestrutura do RNF-02: nenhum segredo versionado e configuração sensível vinda do ambiente."

## Clarifications

### Session 2026-09-25

- Q: O Grana.io deve ser acessível só no computador onde roda, ou também por outros dispositivos da rede local (ex.: celular no mesmo Wi-Fi)? → A: Rede local liberada — outros dispositivos da mesma rede acessam pelo IP da máquina.
- Q: Nesta fase o sistema deve ter só o modo de desenvolvimento (usado também no dia a dia) ou já um modo de uso separado? → A: Só o modo de desenvolvimento por enquanto; o modo de uso é pré-requisito antes de lançar dados financeiros reais.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subir o sistema inteiro com um comando (Priority: P1)

O desenvolvedor clona o repositório numa máquina que tem apenas Docker instalado e, com um
único comando, coloca no ar os três componentes do Grana.io: banco de dados, API e interface
web. Sem instalar linguagens, bibliotecas ou banco na máquina, ele abre o navegador e vê a
interface respondendo, e consegue confirmar que a API está no ar e conectada ao banco.

**Why this priority**: Toda funcionalidade do backlog depende de o ambiente subir. Sem isso não
há onde desenvolver, testar ou demonstrar nenhuma outra feature da Sprint 1 em diante.

**Independent Test**: Num clone limpo do repositório, executar o comando de subida e verificar
que (a) a interface abre no navegador, (b) a verificação de saúde da API responde informando
que a API e o banco estão operacionais.

**Acceptance Scenarios**:

1. **Given** um clone limpo do repositório e Docker em execução, **When** o desenvolvedor executa o comando de subida, **Then** banco, API e interface ficam disponíveis sem nenhum passo manual adicional.
2. **Given** o sistema acabou de subir, **When** o desenvolvedor consulta a verificação de saúde da API, **Then** a resposta indica que a API está no ar e que a conexão com o banco está funcionando.
3. **Given** o sistema acabou de subir, **When** o desenvolvedor abre o endereço da interface no navegador, **Then** a página inicial carrega e exibe se a API está acessível.
4. **Given** o banco ainda está inicializando, **When** a API começa a subir, **Then** a API aguarda o banco ficar pronto em vez de falhar, e o comando de subida termina com todos os componentes no ar.
5. **Given** o sistema está no ar, **When** o desenvolvedor executa o comando de parada, **Then** todos os componentes são encerrados.
6. **Given** o sistema está no ar e outro dispositivo (ex.: celular) está na mesma rede local, **When** esse dispositivo abre a interface pelo IP da máquina, **Then** a página inicial carrega e exibe que a API está acessível, sem nenhuma configuração no dispositivo.

---

### User Story 2 - Dados preservados entre reinicializações (Priority: P1)

O usuário registra dados no sistema, desliga tudo (ou reinicia a máquina) e, ao subir de novo,
encontra os mesmos dados. Os dados só são apagados quando o desenvolvedor pede explicitamente a
remoção dos dados persistidos.

**Why this priority**: O banco é local e é a única cópia dos dados financeiros do usuário
(constituição, Princípio I). Perder dados numa reinicialização inviabiliza o uso real do sistema.

**Independent Test**: Gravar um registro qualquer no banco, parar e subir o sistema de novo, e
confirmar que o registro continua lá; depois, executar o comando explícito de remoção de dados
e confirmar que o banco volta vazio.

**Acceptance Scenarios**:

1. **Given** existem dados gravados, **When** o sistema é parado e iniciado novamente, **Then** todos os dados continuam disponíveis e idênticos.
2. **Given** existem dados gravados, **When** a imagem da API ou da interface é reconstruída, **Then** os dados do banco não são afetados.
3. **Given** existem dados gravados, **When** o desenvolvedor executa o comando documentado de remoção dos dados persistidos, **Then** o banco volta ao estado inicial vazio.

---

### User Story 3 - Configuração por ambiente sem segredos no repositório (Priority: P2)

O desenvolvedor consegue subir o sistema sem criar nenhum arquivo de configuração, usando
valores padrão de desenvolvimento local. Quando quer personalizar (senha do banco,
chave secreta, portas, origem permitida), copia o arquivo de exemplo versionado para um arquivo
local que nunca é versionado. O sistema recusa rodar fora do modo de desenvolvimento com a
chave secreta padrão.

**Why this priority**: Atende a parte de infraestrutura do RNF-02 e o Princípio I da
constituição (segredos só por ambiente). Vem depois das US1/US2 porque o sistema já funciona com
os valores padrão; esta história garante que a personalização seja segura.

**Independent Test**: (a) Subir sem arquivo de configuração local e verificar que funciona;
(b) criar o arquivo local a partir do exemplo com outra senha de banco e verificar que é
usada; (c) confirmar que o arquivo local é ignorado pelo controle de versão; (d) desativar o
modo de desenvolvimento mantendo a chave padrão e verificar que a API se recusa a iniciar com
mensagem clara.

**Acceptance Scenarios**:

1. **Given** não existe arquivo de configuração local, **When** o desenvolvedor sobe o sistema, **Then** tudo funciona com os valores padrão de desenvolvimento.
2. **Given** o desenvolvedor criou o arquivo de configuração local a partir do exemplo, **When** sobe o sistema, **Then** os valores do arquivo local substituem os padrões.
3. **Given** o arquivo de configuração local existe, **When** o desenvolvedor verifica o status do controle de versão, **Then** o arquivo não aparece como candidato a commit.
4. **Given** o modo de desenvolvimento está desativado e a chave secreta é a padrão, **When** a API tenta iniciar, **Then** ela se recusa a subir e informa qual variável precisa ser definida.
5. **Given** o repositório versionado, **When** se busca por senhas, chaves ou tokens reais, **Then** nenhum é encontrado; só existem valores de exemplo claramente identificados.

---

### User Story 4 - Estrutura do banco e testes sem passos manuais (Priority: P2)

Ao subir, a estrutura do banco é criada ou atualizada automaticamente, sem o desenvolvedor
rodar comandos à parte. Da mesma forma, a suíte de testes automatizados roda com um único
comando dentro do ambiente Docker, sem instalar nada na máquina.

**Why this priority**: A constituição exige que a suíte rode com um único comando (Princípio IV)
e que nenhum checkpoint feche com teste falhando; sem isso, o fluxo de marcos de commit das
próximas specs não funciona. Vem depois de US1/US2 porque depende do ambiente já subir.

**Independent Test**: Subir num banco vazio e confirmar que a estrutura inicial foi criada;
rodar o comando de testes e ver a suíte executar e reportar o resultado.

**Acceptance Scenarios**:

1. **Given** um banco vazio, **When** o sistema sobe, **Then** a estrutura do banco é criada automaticamente antes de a API aceitar requisições.
2. **Given** o banco já está com a estrutura atualizada, **When** o sistema sobe novamente, **Then** a subida acontece sem erro e sem alterar dados existentes.
3. **Given** o ambiente Docker disponível, **When** o desenvolvedor executa o comando de testes documentado, **Then** a suíte roda isolada dos dados reais e mostra o resultado (aprovado/reprovado).
4. **Given** a suíte de testes foi executada, **When** o desenvolvedor consulta os dados reais, **Then** nenhum dado foi criado, alterado ou removido pelos testes.

---

### User Story 5 - Documentação de uso do ambiente (Priority: P3)

Uma pessoa que nunca viu o projeto consegue, só lendo o README, subir o sistema, acessar a
interface e a API, parar tudo, rodar os testes e apagar os dados locais.

**Why this priority**: Critério explícito do RNF-01 e base para o RNF-04 (usabilidade). É P3
porque as histórias anteriores já entregam o ambiente funcionando; esta garante que ele seja
reproduzível por outra pessoa (ou por você no futuro).

**Independent Test**: Seguir o README do zero, sem ajuda externa, e completar todas as
operações listadas.

**Acceptance Scenarios**:

1. **Given** o README do repositório, **When** alguém segue as instruções, **Then** consegue subir, acessar, parar, rodar os testes e remover os dados sem consultar outra fonte.
2. **Given** o README, **When** alguém procura os endereços de acesso, **Then** encontra a URL da interface, da API e da verificação de saúde.

---

### Edge Cases

- **Docker não está em execução**: o comando de subida falha com a mensagem do próprio Docker;
  o README orienta a iniciar o Docker antes.
- **Porta já ocupada na máquina** (ex.: outro serviço usando a porta da interface ou da API): a
  subida falha indicando a porta em conflito; as portas expostas são configuráveis pelo arquivo
  de configuração local.
- **Banco demora a ficar pronto** (primeira subida, máquina lenta): a API espera o banco ficar
  saudável em vez de encerrar com erro (US1, cenário 4).
- **Máquina Windows**: arquivos de script e de build precisam funcionar mesmo quando o Git do
  Windows converte finais de linha; o repositório força final de linha LF nesses arquivos
  (lição do projeto edge-computing).
- **Arquivo de configuração local incompleto**: variáveis ausentes caem nos valores padrão de
  desenvolvimento, exceto a chave secreta fora do modo de desenvolvimento (US3, cenário 4).
- **API fora do ar com a interface no ar**: a página inicial informa que a API não está
  acessível, em vez de quebrar ou ficar em branco.
- **Verificação de saúde com o banco fora do ar**: a resposta indica falha na conexão com o
  banco, com status de erro, sem expor detalhes internos (credenciais, endereços, stack traces).
- **Acesso por outro dispositivo da rede**: a interface é aberta pelo IP da máquina; as chamadas
  à API precisam chegar à máquina que roda o sistema, e não ao próprio dispositivo (o endereço
  "localhost" no celular aponta para o celular).
- **IP da máquina muda** (ex.: roteador atribui outro endereço): o acesso pela rede continua
  funcionando pelo novo IP sem reconstruir imagens nem editar configuração.
- **Firewall do sistema operacional bloqueia as portas**: outros dispositivos não conseguem
  acessar; o README orienta a liberar as portas da interface e da API na rede privada.
- **Rede local antes do login existir**: até a spec 003 (login), qualquer dispositivo da rede
  alcança a API; nesta spec a API só expõe a verificação de saúde, sem dados de usuários.
- **Banco de dados**: nunca acessível por outros dispositivos, mesmo com a rede local liberada.
- **Erros detalhados visíveis na rede local**: no modo de desenvolvimento, uma falha pode exibir
  detalhes técnicos a qualquer dispositivo da rede. Risco aceito enquanto não há dados reais;
  mitigado pelo futuro modo de uso (ver Assumptions).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST subir banco de dados, API e interface web com um único comando, a partir de um clone limpo, exigindo apenas Docker instalado na máquina.
- **FR-002**: O sistema MUST encerrar todos os componentes com um único comando de parada.
- **FR-003**: A API MUST aguardar o banco estar pronto antes de iniciar, sem falhar na primeira subida.
- **FR-004**: A estrutura do banco MUST ser criada/atualizada automaticamente a cada subida, antes de a API aceitar requisições, sem alterar dados existentes.
- **FR-005**: Os dados do banco MUST persistir entre paradas, reinicializações da máquina e reconstrução das imagens da API e da interface.
- **FR-006**: MUST existir um comando documentado para remover explicitamente os dados persistidos; nenhuma outra operação rotineira pode apagá-los.
- **FR-007**: A API MUST expor uma verificação de saúde pública (sem autenticação) que informe se a API está operacional e se a conexão com o banco funciona, sem expor dados sensíveis ou detalhes internos.
- **FR-008**: A interface web MUST ter uma página inicial provisória que exiba o nome do sistema e se a API está acessível. Por padrão, a interface MUST localizar a API a partir do mesmo endereço pelo qual ela própria foi aberta (local ou IP da rede), sem endereço de máquina fixo; um endereço explícito da API pode ser definido por configuração para cenários futuros (RNF-08).
- **FR-009**: Toda configuração que varia por ambiente (credenciais do banco, chave secreta, modo de desenvolvimento, hosts e origens permitidas, endereço da API, portas expostas) MUST vir de variáveis de ambiente.
- **FR-010**: O sistema MUST funcionar sem arquivo de configuração local, usando valores padrão de desenvolvimento; quando o arquivo local existir, seus valores MUST prevalecer.
- **FR-011**: O repositório MUST versionar um arquivo de exemplo de configuração com todas as variáveis documentadas, e MUST ignorar o arquivo de configuração local.
- **FR-012**: A API MUST se recusar a iniciar fora do modo de desenvolvimento se a chave secreta for o valor padrão, com mensagem indicando a variável a definir.
- **FR-013**: A API MUST aceitar requisições do navegador apenas a partir da própria interface do Grana.io, seja ela acessada pelo endereço local ou pelo IP da máquina na rede local; origens adicionais só por configuração.
- **FR-014**: A suíte de testes automatizados MUST rodar com um único comando dentro do ambiente Docker, isolada dos dados reais.
- **FR-015**: No modo de desenvolvimento, alterações no código da API e da interface MUST ser refletidas sem reconstruir as imagens.
- **FR-016**: O repositório MUST garantir final de linha LF em scripts e arquivos de build, para funcionar em Windows e Linux.
- **FR-017**: O README MUST documentar: pré-requisitos, como subir, parar, acessar (URLs da interface, da API e da verificação de saúde), acessar por outro dispositivo da rede local (como descobrir o IP e liberar o firewall), rodar os testes, personalizar a configuração e remover os dados locais.
- **FR-018**: A interface e a API MUST ser acessíveis por outros dispositivos da mesma rede local, pelo IP da máquina, sem configuração nos dispositivos clientes e sem precisar reconfigurar quando o IP da máquina mudar.
- **FR-019**: O banco de dados MUST NOT ficar acessível fora do ambiente Docker, nem pela máquina nem pela rede local.

### Key Entities

- **Dados persistidos**: o conjunto de dados do banco local, que sobrevive a reinicializações e
  só é removido por comando explícito. Nesta feature ainda não há entidades de domínio; elas
  chegam nas próximas specs.
- **Configuração de ambiente**: conjunto de variáveis (credenciais, chave secreta, modo,
  origens, endereço da API, portas) com valores padrão de desenvolvimento, sobrescritíveis pelo
  arquivo local não versionado.
- **Verificação de saúde**: resposta pública e mínima que indica o estado da API e da conexão
  com o banco.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A partir de um clone limpo, com Docker instalado, o sistema está utilizável (interface abrindo e API saudável) com 1 comando e em até 10 minutos na primeira execução (incluindo downloads).
- **SC-002**: Nas subidas seguintes, o sistema está utilizável em até 1 minuto.
- **SC-003**: Em 5 ciclos seguidos de parar e subir, 100% dos dados gravados permanecem idênticos.
- **SC-004**: Nenhum segredo real é encontrado no repositório versionado (verificação por busca de senhas, chaves e tokens).
- **SC-005**: A suíte de testes completa roda com 1 comando e não altera nenhum dado real.
- **SC-006**: Uma pessoa que nunca viu o projeto completa, só com o README, as operações de subir, acessar, parar, testar e remover dados na primeira tentativa.
- **SC-007**: O ambiente sobe com sucesso tanto em Windows quanto em Linux.
- **SC-008**: Um celular na mesma rede Wi-Fi abre a interface pelo IP da máquina e vê a API acessível, sem nenhuma configuração no celular.

## Assumptions

- A máquina tem Docker com Docker Compose instalado; nenhuma outra dependência (linguagens, banco)
  é exigida na máquina.
- Esta feature entrega apenas o **esqueleto** da API e da interface (verificação de saúde e
  página inicial provisória). Usuários, login e telas reais chegam nas specs 002 a 005.
- Há um único modo de execução nesta fase: o modo de desenvolvimento (recarga automática,
  mensagens de erro detalhadas). Um modo de uso separado (versão otimizada, sem páginas de erro
  detalhadas na rede local) está fora do escopo desta spec, mas é **pré-requisito antes de
  lançar dados financeiros reais** no sistema; deve virar item próprio no backlog.
- A verificação de saúde é a única rota pública além das futuras rotas de cadastro e login
  (RNF-02); ela não retorna dados de usuários nem detalhes internos.
- Os valores padrão de desenvolvimento (inclusive a chave secreta padrão) são aceitáveis
  porque o sistema roda só localmente; o bloqueio do FR-012 impede seu uso fora do modo de
  desenvolvimento.
- Backup e restauração dos dados (RNF-06) e logging estruturado (RNF-07) ficam fora do escopo
  desta spec (Sprint 6).
- Portas padrão: interface em 5173 e API em 8000, acessíveis também pela rede local; o banco
  não é exposto fora do ambiente Docker (FR-019).
- A rede local é uma rede doméstica confiável. Expor o sistema à internet (redirecionamento de
  portas no roteador, túneis) está fora de escopo e não é suportado.
