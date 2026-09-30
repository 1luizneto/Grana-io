# Feature Specification: Login e Logout

**Feature Branch**: `003-login-logout`

**Created**: 2026-09-30

**Status**: Draft

**Input**: User description: "US-02: Como usuário, quero fazer login e logout, para que o sistema saiba quem está acessando. Critérios: login com e-mail e senha retorna um token válido; credenciais inválidas exibem mensagem genérica (sem revelar se o e-mail existe); o token expira após um período definido e pode ser renovado; o logout invalida a sessão; rotas protegidas exigem sessão válida."

## Clarifications

### Session 2026-09-30

- Q: Quanto tempo duram a credencial de acesso e a de renovação? → A: Acesso de 30 minutos e
  renovação de 7 dias por padrão, ajustáveis por configuração de ambiente.
- Q: O sistema deve limitar tentativas de login em pouco tempo? → A: Sim, limite por dispositivo.
  Depois de 10 tentativas em 1 minuto, o login daquele dispositivo recebe "Muitas tentativas. Tente
  novamente em instantes." até a janela passar. A conta não é bloqueada.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entrar com e-mail e senha (Priority: P1)

Uma pessoa com conta (US-01) informa e-mail e senha e passa a ter uma **sessão**: o sistema
reconhece quem ela é nas próximas ações, sem pedir a senha de novo a cada passo.

**Why this priority**: sem login não existe "usuário atual". Nenhum dado financeiro pode ser
lido ou gravado com dono (constituição, Princípio II; US-03).

**Independent Test**: com uma conta criada pelo cadastro, entrar com e-mail e senha e verificar
que (a) o sistema devolve uma credencial de sessão, (b) com ela é possível consultar a própria
conta, (c) a resposta não contém a senha.

**Acceptance Scenarios**:

1. **Given** uma conta ativa `ana@exemplo.com`, **When** a pessoa entra com esse e-mail e a senha correta, **Then** recebe uma credencial de acesso e uma credencial de renovação, além do seu nome e e-mail.
2. **Given** uma conta `ana@exemplo.com`, **When** a pessoa entra com `ANA@Exemplo.com` ou `  ana@exemplo.com  ` e a senha correta, **Then** o login funciona da mesma forma.
3. **Given** uma sessão válida, **When** a pessoa consulta a própria conta, **Then** vê o seu nome e e-mail, e nada de outra conta.
4. **Given** um login bem-sucedido, **When** se consulta a conta, **Then** a data do último acesso foi atualizada.

---

### User Story 2 - Recusar credenciais inválidas sem revelar contas (Priority: P1)

Se o e-mail não existe, a senha está errada ou a conta está desativada, o login é recusado com
**a mesma mensagem genérica**, para que ninguém descubra quais e-mails têm conta.

**Why this priority**: critério explícito do backlog e proteção básica dos dados (RNF-02).

**Independent Test**: tentar entrar com e-mail inexistente, com senha errada e com conta
desativada, e verificar que as três respostas são idênticas e nenhuma cria sessão.

**Acceptance Scenarios**:

1. **Given** um e-mail que não tem conta, **When** alguém tenta entrar, **Then** o login é recusado com "E-mail ou senha incorretos.".
2. **Given** uma conta existente, **When** alguém tenta entrar com a senha errada, **Then** a resposta é idêntica à do cenário 1 (mesma mensagem e mesmo código de resposta).
3. **Given** uma conta desativada, **When** a dona tenta entrar com a senha correta, **Then** a resposta é idêntica à do cenário 1.
4. **Given** um login sem e-mail ou sem senha, **When** é enviado, **Then** é recusado com "Este campo é obrigatório." no campo ausente, sem consultar contas.

---

### User Story 3 - Proteger o que exige sessão (Priority: P1)

Tudo no sistema, exceto cadastro, login, renovação da sessão e verificação de saúde, só responde
a quem tem uma sessão válida. Sem sessão, ou com uma credencial inválida ou vencida, a
requisição é recusada com mensagem clara, e a interface (US-26) saberá que precisa levar a
pessoa ao login.

**Why this priority**: critério do RNF-02 ("autenticação em todas as rotas, exceto login e
cadastro") e base para o isolamento por usuário (US-03).

**Independent Test**: consultar a própria conta sem credencial, com credencial adulterada e com
credencial vencida, e verificar a recusa em todos os casos; depois, com credencial válida, ver
a consulta funcionar.

**Acceptance Scenarios**:

1. **Given** nenhuma credencial, **When** alguém consulta a própria conta, **Then** a requisição é recusada como "não autenticado", com mensagem em português.
2. **Given** uma credencial adulterada ou inventada, **When** é usada, **Then** a requisição é recusada da mesma forma.
3. **Given** uma credencial de acesso vencida, **When** é usada, **Then** a requisição é recusada, e a resposta permite distinguir "sessão vencida" para a interface tentar renovar.
4. **Given** as rotas públicas (cadastro, login, renovação, verificação de saúde), **When** acessadas sem credencial, **Then** continuam funcionando.

---

### User Story 4 - Sessão que expira e pode ser renovada (Priority: P2)

A credencial de acesso dura pouco tempo, para limitar o estrago se vazar. Antes de a sessão
acabar de vez, a interface pode renová-la com a credencial de renovação, sem pedir a senha de
novo. Quando a renovação também vence, é preciso entrar de novo.

**Why this priority**: critério do backlog ("o token expira após um período definido e pode ser
renovado"). Vem depois de US1 a US3 porque a sessão já funciona sem renovação, só dura menos.

**Independent Test**: entrar, renovar e verificar que a nova credencial de acesso funciona;
verificar que a credencial de renovação antiga não serve mais; simular o vencimento e verificar
que a renovação é recusada.

**Acceptance Scenarios**:

1. **Given** uma credencial de renovação válida, **When** a interface pede a renovação, **Then** recebe uma nova credencial de acesso e uma nova credencial de renovação.
2. **Given** uma credencial de renovação já usada numa renovação, **When** é usada de novo, **Then** é recusada (cada renovação troca a credencial).
3. **Given** uma credencial de renovação vencida ou inválida, **When** é usada, **Then** é recusada com mensagem clara, e a pessoa precisa entrar de novo.
4. **Given** uma conta desativada depois do login, **When** a sessão tenta ser renovada, **Then** a renovação é recusada.

---

### User Story 5 - Sair do sistema (Priority: P2)

A pessoa sai do sistema e a sessão deixa de poder ser renovada, mesmo que alguém tenha copiado a
credencial de renovação.

**Why this priority**: critério do backlog ("o logout invalida a sessão"). Importante em
dispositivos compartilhados da casa.

**Independent Test**: entrar, sair e verificar que a credencial de renovação daquela sessão não
funciona mais; verificar que uma sessão aberta em outro dispositivo continua funcionando.

**Acceptance Scenarios**:

1. **Given** uma sessão ativa, **When** a pessoa sai informando a sua credencial de renovação, **Then** a saída é confirmada e essa credencial de renovação é invalidada.
2. **Given** uma sessão encerrada, **When** alguém tenta renová-la, **Then** a renovação é recusada.
3. **Given** a mesma conta com sessões em dois dispositivos, **When** a pessoa sai em um deles, **Then** a sessão do outro dispositivo continua válida.
4. **Given** uma tentativa de saída com uma credencial de renovação inválida, vencida ou de outra pessoa, **When** é enviada, **Then** é recusada sem afetar nenhuma sessão válida.

---

### Edge Cases

- **Credencial de acesso após a saída**: a credencial de acesso da sessão encerrada continua
  aceita até vencer, ou seja, por no máximo 30 minutos no padrão (FR-006). A interface a descarta na saída (US-26).
  Isso é aceito para evitar consultar uma lista de bloqueio a cada requisição.
- **E-mail com maiúsculas ou espaços** no login: tratado como o mesmo e-mail (US1, cenário 2),
  seguindo a normalização do cadastro (spec 002).
- **Conta desativada com sessão aberta**: novas requisições com a credencial de acesso dela são
  recusadas, e a renovação também (US4, cenário 4).
- **Várias tentativas de login em pouco tempo**: a partir da 11ª tentativa no mesmo minuto, o
  mesmo dispositivo recebe "Muitas tentativas. Tente novamente em instantes.", inclusive se a
  senha estiver certa, até a janela de 1 minuto passar (FR-015). Outros dispositivos e a própria
  conta não são afetados; a conta nunca é bloqueada, para que ninguém consiga trancar a conta de
  outra pessoa errando a senha de propósito.
- **Senha nunca devolvida nem registrada**: nem respostas, nem erros, nem logs contêm a senha
  (constituição, Princípio I). As credenciais de sessão também não são registradas em logs.
- **Relógio**: os vencimentos usam o horário do servidor, e não dependem do relógio do
  dispositivo da pessoa.
- **Credenciais enviadas por meio inseguro**: o sistema roda em HTTP na rede local doméstica
  (spec 001), e o risco é aceito até o modo de uso (RNF-09).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir entrar informando e-mail e senha; com credenciais corretas de uma conta ativa, MUST devolver uma credencial de acesso, uma credencial de renovação, e o nome e o e-mail da conta.
- **FR-002**: O e-mail do login MUST ser tratado sem diferenciar maiúsculas de minúsculas e sem espaços nas pontas.
- **FR-003**: E-mail inexistente, senha errada e conta desativada MUST produzir exatamente a mesma resposta: a mensagem "E-mail ou senha incorretos." e o mesmo código de resposta. Nenhum desses casos cria sessão.
- **FR-004**: Login sem e-mail ou sem senha MUST ser recusado com "Este campo é obrigatório." em cada campo ausente.
- **FR-005**: Um login bem-sucedido MUST registrar a data e hora do último acesso da conta.
- **FR-006**: Por padrão, a credencial de acesso MUST valer 30 minutos e a credencial de renovação 7 dias, contados a partir da emissão; os dois prazos MUST poder ser ajustados por configuração de ambiente, sem alterar código.
- **FR-007**: Com uma credencial de renovação válida, o sistema MUST devolver uma nova credencial de acesso e uma nova credencial de renovação, e MUST invalidar a credencial de renovação usada (cada uma serve uma única vez).
- **FR-008**: Credenciais de renovação vencidas, inválidas, já usadas, encerradas por saída ou de conta desativada MUST ser recusadas com mensagem clara em português.
- **FR-009**: A saída MUST invalidar a credencial de renovação informada, de modo que ela não possa mais ser usada para renovar; outras sessões da mesma conta MUST continuar válidas.
- **FR-010**: Todas as funcionalidades do sistema MUST exigir uma credencial de acesso válida, exceto cadastro (spec 002), login, renovação e verificação de saúde (spec 001).
- **FR-011**: Requisições sem credencial, com credencial inválida ou vencida a funcionalidades protegidas MUST ser recusadas como "não autenticado", com mensagem em português; a credencial vencida MUST ser distinguível, para a interface tentar renovar.
- **FR-012**: Com uma sessão válida, a pessoa MUST poder consultar a própria conta (nome e e-mail), e somente a própria.
- **FR-013**: Senhas e credenciais de sessão MUST NOT aparecer em logs nem em mensagens de erro; a senha MUST NOT aparecer em respostas.
- **FR-014**: Uma conta desativada MUST perder o acesso: suas credenciais de acesso e de renovação passam a ser recusadas, mesmo que ainda não tenham vencido.
- **FR-015**: O login MUST aceitar no máximo 10 tentativas por minuto de um mesmo dispositivo (endereço de rede), certas ou erradas; acima disso MUST responder "Muitas tentativas. Tente novamente em instantes." até a janela passar, sem bloquear a conta nem afetar outros dispositivos. O limite MUST poder ser ajustado por configuração de ambiente.

### Key Entities

- **Sessão**: o vínculo entre uma pessoa autenticada e um dispositivo. É representada por uma
  credencial de acesso (curta, apresentada a cada requisição) e uma credencial de renovação
  (mais longa, usada só para obter novas credenciais). Uma conta pode ter várias sessões.
- **Credencial de renovação invalidada**: registro de uma credencial de renovação que não pode
  mais ser usada, por ter sido trocada numa renovação ou encerrada na saída.
- **Usuário** (spec 002): ganha o uso da data do último acesso.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa com conta entra no sistema em até 30 segundos, na primeira tentativa, com os dados corretos.
- **SC-002**: Em 100% das tentativas com e-mail inexistente, senha errada ou conta desativada, a resposta é idêntica e nenhuma sessão é criada.
- **SC-003**: 100% das requisições sem credencial válida a funcionalidades protegidas são recusadas; 100% das públicas continuam acessíveis sem credencial.
- **SC-004**: Depois da saída, 100% das tentativas de renovar a sessão encerrada são recusadas, e as sessões de outros dispositivos seguem funcionando.
- **SC-005**: Com os prazos padrão, uma pessoa que usa o sistema ao menos uma vez a cada 7 dias no mesmo dispositivo não precisa digitar a senha de novo nesse período; uma credencial de acesso copiada deixa de funcionar em até 30 minutos.
- **SC-006**: Nenhuma senha ou credencial de sessão aparece nos logs do sistema.
- **SC-007**: Um mesmo dispositivo consegue fazer no máximo 10 tentativas de login por minuto; adivinhar uma senha por tentativa e erro fica limitado a 600 tentativas por hora por dispositivo.

## Assumptions

- **Escopo só da API**: esta spec entrega o login, a renovação, a saída e a proteção das
  funcionalidades, verificáveis por requisições documentadas no contrato da API. Ficam para a
  US-26 (spec 005) as telas de login, o redirecionamento ao login quando não há sessão, o descarte
  das credenciais no navegador ao sair e a renovação automática pela interface. Os critérios do
  backlog "O logout ... redireciona para o login" e "Rotas protegidas redirecionam para o login"
  ficam registrados como cobertos pela US-26.
- A consulta à própria conta é o recurso protegido mínimo desta spec. Ela serve para validar a
  sessão e será usada pela interface (US-26) para mostrar quem está conectado. Alterar dados da
  conta é a US-04.
- A verificação de saúde continua pública (spec 001). É uma exceção ao critério do RNF-02
  "autenticação em todas as rotas, exceto login e cadastro", porque não expõe dados.
- O método de sessão segue a constituição (credenciais assinadas, com login por e-mail). O sistema
  não usa cookies de sessão nesta spec.
- Trocar a senha e invalidar as sessões antigas é a US-04.
- Sem "lembrar de mim" separado: a duração da renovação define por quanto tempo a pessoa fica
  conectada sem digitar a senha.
- O limite de tentativas vale só para o login (Clarifications). Cadastro e renovação não têm
  limite nesta spec. O dispositivo é identificado pelo endereço de rede de onde vem a requisição;
  dispositivos atrás do mesmo endereço compartilham o limite, o que é aceitável numa rede doméstica.
- Não há bloqueio de conta por senha errada (Clarifications).
