# Feature Specification: Telas de Login e Cadastro

**Feature Branch**: `005-telas-login-cadastro`

**Created**: 2026-10-05

**Status**: Draft

**Input**: User description: "US-26: Como usuário, quero telas de login e cadastro, para acessar o sistema pelo navegador. Critérios: telas de login e cadastro cobrindo US-01 e US-02; erros de validação aparecem ao lado de cada campo; a sessão persiste ao recarregar a página até o token expirar; o layout base da aplicação (menu, cabeçalho com usuário logado e logout) fica pronto. Também cobre os critérios de tela da US-02: o logout invalida a sessão no frontend e redireciona para o login; rotas protegidas redirecionam para o login quando não há sessão."

## Clarifications

### Session 2026-10-05

- Q: Depois do cadastro, a pessoa entra direto ou vai para o login? → A: Entra direto no sistema,
  usando o e-mail e a senha que acabou de informar, e chega à página inicial.
- Q: Fechar o navegador encerra a sessão? → A: Não. A pessoa continua conectada, mesmo fechando o
  navegador, até a sessão não poder mais ser renovada (7 dias sem uso, no padrão da spec 003) ou
  até escolher "Sair".
- Q: A interface ganha testes automatizados nesta spec? → A: Sim, para a lógica de sessão
  (renovação única, proteção das páginas, saída e descarte da sessão) e para a exibição dos erros
  por campo. O visual das telas fica na verificação manual do quickstart.
- Q: A credencial de renovação pode ficar guardada no navegador num lugar legível pela própria
  interface, ou a API deve passar a guardá-la num cookie protegido? → A: Fica no armazenamento
  do navegador, legível pela interface; a API não muda. O risco é aceito e registrado (Assumptions).

## User Scenarios & Testing *(mandatory)*

> **Contexto**: as specs 002 e 003 entregaram cadastro, login, renovação e saída **pela API**.
> Esta spec é a primeira com telas de verdade: a pessoa passa a usar o sistema só pelo navegador,
> sem comandos. A interface só exibe o que a API devolve, sem regras próprias (constituição,
> Princípio V).

### User Story 1 - Entrar pela tela de login (Priority: P1)

A pessoa abre o sistema, informa e-mail e senha numa tela de login e chega à página inicial,
já identificada pelo nome no cabeçalho.

**Why this priority**: é a porta de entrada. Sem ela, nada do que vem depois (gastos, cenários)
pode ser usado pelo navegador.

**Independent Test**: com uma conta existente, abrir o sistema, entrar com e-mail e senha e ver a
página inicial com o nome da pessoa no cabeçalho.

**Acceptance Scenarios**:

1. **Given** uma conta `ana@exemplo.com`, **When** a pessoa informa e-mail e senha corretos e confirma, **Then** chega à página inicial e vê "Ana Souza" no cabeçalho.
2. **Given** e-mail inexistente ou senha errada, **When** a pessoa confirma, **Then** vê "E-mail ou senha incorretos." acima do formulário, continua na tela de login e o e-mail digitado é mantido (a senha é apagada).
3. **Given** e-mail ou senha em branco, **When** a pessoa confirma, **Then** vê "Este campo é obrigatório." ao lado de cada campo vazio.
4. **Given** muitas tentativas seguidas, **When** o sistema recusa por excesso, **Then** a pessoa vê "Muitas tentativas. Tente novamente em instantes."
5. **Given** o login em andamento, **When** a pessoa espera a resposta, **Then** o botão mostra que está processando e não aceita um segundo clique.

---

### User Story 2 - Ficar conectado e proteger as páginas (Priority: P1)

Depois de entrar, a pessoa continua conectada ao recarregar a página ou navegar, sem digitar a
senha de novo, enquanto a sessão for válida. Quem não está conectado e tenta abrir uma página do
sistema é levado ao login e, depois de entrar, volta para a página que queria.

**Why this priority**: sem isso, a pessoa perderia a sessão a cada recarga, e as páginas ficariam
visíveis sem login (critérios da US-02 e da US-26).

**Independent Test**: entrar, recarregar a página e continuar conectado; em outra janela anônima,
abrir direto o endereço de uma página protegida e cair no login; entrar e voltar à página pedida.

**Acceptance Scenarios**:

1. **Given** uma pessoa conectada, **When** recarrega a página, **Then** continua conectada, na mesma página.
2. **Given** ninguém conectado, **When** alguém abre o endereço de uma página protegida, **Then** é levado ao login e, ao entrar, volta para aquela página.
3. **Given** uma pessoa conectada há mais de 30 minutos (credencial de acesso vencida) e com a sessão ainda válida, **When** usa o sistema, **Then** continua usando normalmente, sem perceber a renovação.
4. **Given** uma sessão que não pode mais ser renovada (vencida, encerrada ou conta desativada), **When** a pessoa usa o sistema, **Then** é levada ao login com o aviso "Sua sessão expirou. Entre novamente."
5. **Given** uma pessoa conectada, **When** abre a tela de login ou de cadastro, **Then** é levada à página inicial.

---

### User Story 3 - Criar conta pela tela de cadastro (Priority: P1)

Uma pessoa sem conta preenche nome, e-mail, senha e confirmação numa tela de cadastro. Erros
aparecem ao lado de cada campo, todos de uma vez, com a mensagem que a API devolve.

**Why this priority**: sem a tela, uma pessoa nova só conseguiria criar conta por comando (US-01).

**Independent Test**: abrir o cadastro pela tela de login, criar uma conta nova e, em seguida,
tentar de novo com o mesmo e-mail e com senhas diferentes, vendo os erros ao lado de cada campo.

**Acceptance Scenarios**:

1. **Given** a tela de login, **When** a pessoa escolhe "Criar conta", **Then** vai para a tela de cadastro (e da tela de cadastro consegue voltar ao login).
2. **Given** dados válidos, **When** a pessoa confirma o cadastro, **Then** a conta é criada, a pessoa entra no sistema automaticamente e chega à página inicial com o próprio nome no cabeçalho.
3. **Given** um e-mail já cadastrado, senha curta e confirmação diferente, **When** a pessoa confirma, **Then** vê, ao mesmo tempo, cada mensagem ao lado do seu campo, e os dados digitados (exceto as senhas) continuam preenchidos.
4. **Given** o cadastro fechado no sistema, **When** a pessoa tenta se cadastrar, **Then** vê "O cadastro de novas contas está desativado neste sistema." acima do formulário.

---

### User Story 4 - Sair do sistema (Priority: P2)

A pessoa conectada escolhe "Sair" no cabeçalho, a sessão é encerrada e ela volta ao login.

**Why this priority**: necessária em computador compartilhado (critério da US-02), mas o sistema
já é útil sem ela no dia a dia.

**Independent Test**: entrar, sair, tentar voltar com o botão "voltar" do navegador e cair no login.

**Acceptance Scenarios**:

1. **Given** uma pessoa conectada, **When** escolhe "Sair", **Then** volta para a tela de login com o aviso "Você saiu do sistema."
2. **Given** a pessoa acabou de sair, **When** usa o "voltar" do navegador ou recarrega, **Then** continua no login e não vê dados da sessão anterior.
3. **Given** a saída, **When** alguém tenta reaproveitar a sessão encerrada, **Then** ela não pode mais ser renovada (spec 003).
4. **Given** a API indisponível no momento da saída, **When** a pessoa escolhe "Sair", **Then** a sessão é descartada no navegador mesmo assim e ela vai para o login.

---

### User Story 5 - Layout base da aplicação (Priority: P2)

Todas as páginas do sistema (depois do login) compartilham o mesmo layout: um cabeçalho com o
nome do sistema, o nome da pessoa conectada e o botão "Sair", e um menu de navegação. O menu hoje
leva só à página inicial e cresce a cada nova funcionalidade.

**Why this priority**: as próximas telas (mês, gastos, cenários) vão se encaixar nesse layout; ele
precisa existir antes delas, mas não muda o login em si.

**Independent Test**: entrar e ver cabeçalho, nome, "Sair" e menu; numa tela estreita (celular),
o layout continua utilizável, sem rolagem horizontal.

**Acceptance Scenarios**:

1. **Given** uma pessoa conectada, **When** está em qualquer página do sistema, **Then** vê o cabeçalho com "Grana.io", o próprio nome e "Sair", e o menu com "Início".
2. **Given** uma tela de 360 px de largura, **When** a pessoa usa o login, o cadastro ou o layout, **Then** todos os campos e botões ficam visíveis e utilizáveis, sem rolagem horizontal.
3. **Given** as telas de login e cadastro, **When** exibidas, **Then** não mostram o menu nem o cabeçalho de pessoa conectada.

---

### Edge Cases

- **API fora do ar ou sem rede** no login ou no cadastro: a pessoa vê "Não foi possível falar com o
  servidor. Tente novamente." e os dados digitados continuam no formulário.
- **Recarregar a página com a sessão vencida**: a interface tenta renovar uma vez; se não der, leva
  ao login com "Sua sessão expirou. Entre novamente."
- **Várias abas abertas**: sair numa aba não fecha as outras na hora; a outra aba percebe na
  próxima ação e leva ao login. Se duas abas renovarem a credencial ao mesmo tempo, a que perder a
  corrida usa a credencial nova que a outra gravou, sem desconectar a pessoa.
- **Várias requisições ao mesmo tempo com a credencial vencida**: a renovação acontece uma única
  vez e as requisições seguem com a credencial nova. Como cada renovação vale uma única vez (spec
  003), duas renovações em paralelo encerrariam a sessão.
- **Endereço inexistente**: a pessoa vê "Página não encontrada." com um link para a página inicial.
- **Senha** nunca fica guardada no navegador pela aplicação, nunca aparece em endereços nem em
  mensagens, e o campo de senha não mostra o que é digitado.
- **E-mail com maiúsculas ou espaços**: aceito como está; a API normaliza (specs 002 e 003).
- **Enter no teclado** confirma o formulário; todos os campos têm rótulo visível e podem ser
  usados só pelo teclado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST ter uma tela de login com e-mail e senha, que entra no sistema e leva à página inicial (ou à página que a pessoa tentou abrir antes).
- **FR-002**: O sistema MUST ter uma tela de cadastro com nome, e-mail, senha e confirmação de senha, acessível pela tela de login, e vice-versa.
- **FR-003**: Erros de validação MUST aparecer ao lado do campo a que se referem, todos de uma vez, com o texto devolvido pelo servidor; erros que não são de um campo MUST aparecer acima do formulário.
- **FR-004**: Depois de uma tentativa recusada, os dados digitados MUST continuar no formulário, exceto senha e confirmação, que MUST ser apagadas.
- **FR-005**: Enquanto um envio está em andamento, o botão MUST indicar processamento e MUST NOT aceitar novo envio.
- **FR-006**: A sessão MUST continuar ao recarregar a página, ao navegar e ao fechar e reabrir o navegador, até não poder mais ser renovada (7 dias sem uso, no padrão da spec 003) ou até a pessoa sair.
- **FR-007**: Quando a credencial de acesso vencer, a interface MUST renová-la sozinha, uma única vez mesmo com várias requisições simultâneas, sem interromper a pessoa.
- **FR-008**: Quando a sessão não puder ser renovada, a interface MUST descartá-la e levar ao login com "Sua sessão expirou. Entre novamente."
- **FR-009**: Toda página, exceto login, cadastro e "página não encontrada", MUST exigir sessão; sem sessão, a pessoa MUST ser levada ao login e, depois de entrar, de volta à página pedida.
- **FR-010**: Uma pessoa conectada que abrir login ou cadastro MUST ser levada à página inicial.
- **FR-011**: "Sair" MUST encerrar a sessão no servidor, descartar a sessão no navegador (mesmo se o servidor não responder) e levar ao login com "Você saiu do sistema."
- **FR-012**: As páginas protegidas MUST compartilhar um layout com cabeçalho ("Grana.io", nome da pessoa conectada, "Sair") e menu de navegação (hoje, "Início").
- **FR-013**: Login, cadastro e layout MUST funcionar em telas a partir de 360 px de largura, sem rolagem horizontal.
- **FR-014**: Todos os textos da interface MUST estar em português do Brasil; campos MUST ter rótulos visíveis e o uso só pelo teclado MUST ser possível.
- **FR-015**: Falha de comunicação com o servidor MUST mostrar "Não foi possível falar com o servidor. Tente novamente." sem perder o que foi digitado.
- **FR-016**: A senha MUST NOT ser guardada pela aplicação no navegador nem aparecer em endereços ou mensagens. As credenciais de sessão MUST NOT aparecer em endereços, e a interface MUST NOT carregar scripts ou recursos de terceiros (condição do risco aceito em Assumptions).
- **FR-017**: A página inicial MUST mostrar uma saudação com o nome da pessoa e o aviso de que os recursos financeiros chegam nas próximas entregas.
- **FR-018**: Um endereço inexistente MUST mostrar "Página não encontrada." com link para a página inicial.
- **FR-019**: Depois de um cadastro aceito, a interface MUST entrar no sistema automaticamente com o e-mail e a senha informados e levar à página inicial. Se essa entrada falhar, MUST levar ao login com o e-mail preenchido e o aviso "Conta criada. Entre com sua senha."
- **FR-020**: A lógica de sessão (renovação única, proteção das páginas, saída e descarte da sessão) e a exibição dos erros por campo MUST ter testes automatizados, executáveis com um único comando no Docker.

### Key Entities

- **Sessão no navegador**: o que a interface guarda no armazenamento do navegador, que sobrevive a
  fechar e reabrir (Clarifications), para manter a pessoa conectada: as credenciais de acesso e
  de renovação (spec 003) e o nome e e-mail da pessoa. Nunca a senha. É apagada ao sair e quando
  a sessão não pode mais ser renovada.
- **Usuário** (specs 002 e 003): nome e e-mail exibidos no cabeçalho.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa nova cria a conta e chega à página inicial em até 2 minutos, sem ajuda e sem usar comandos.
- **SC-002**: Uma pessoa com conta entra no sistema em até 30 segundos.
- **SC-003**: Em 100% das recargas de página, e ao fechar e reabrir o navegador, com sessão válida, a pessoa continua conectada, sem digitar a senha.
- **SC-004**: Em 100% das tentativas de abrir uma página protegida sem sessão, a pessoa vê o login, e nenhum dado da área protegida aparece antes disso.
- **SC-005**: Depois de "Sair", 0 páginas protegidas ficam acessíveis pelo "voltar" ou pela recarga.
- **SC-006**: Todos os erros de cadastro de uma tentativa aparecem de uma vez, cada um ao lado do seu campo.
- **SC-007**: Login, cadastro e layout são utilizáveis do começo ao fim numa tela de 360 px, sem rolagem horizontal.

## Assumptions

- **Escopo da interface**: login, cadastro, saída, proteção das páginas, renovação automática e o
  layout base com uma página inicial provisória. Dados financeiros e as demais telas são das USs
  seguintes (US-27 em diante).
- **API pronta**: cadastro, login, renovação, saída e consulta da própria conta já existem (specs
  002 e 003). A única mudança na API é de texto: campo **vazio** passa a responder "Este campo é
  obrigatório.", igual ao campo ausente, no login, no cadastro e na renovação (achado da T022;
  antes vinha o padrão do DRF, "Este campo pode não estar em branco.").
- **Mensagens vindas da API**: os textos de erro de validação e de recusa vêm da API e são exibidos
  como estão (constituição, Princípio V). Os textos próprios da interface (sessão expirada, saiu
  do sistema, falha de comunicação, página não encontrada) são definidos aqui.
- **Menu**: começa só com "Início"; cada tela nova entra no menu na sua própria US.
- **Indicador de saúde**: o aviso de "API acessível" da spec 001 deixa de ser o conteúdo da página
  inicial; ele pode continuar como um detalhe discreto do layout ou sair, decisão do plano.
- **Visual**: limpo e funcional, sem identidade visual elaborada; a refinação visual é do RNF-04.
- **Rede local por HTTP** (spec 001): as credenciais trafegam sem criptografia até o modo de uso
  (RNF-09); risco já aceito na spec 003.
- **Esquecer a senha**: fora do escopo (não está no backlog; o sistema não envia e-mails).
- **Acesso pelo celular**: o layout funciona em tela estreita (FR-013), mas o problema de acesso
  pela rede local da spec 001 continua pendente e não é desta spec.
- **Verificação** (Clarifications): a interface ganha testes automatizados para a lógica de sessão
  e a exibição de erros (FR-020). O visual, o layout em tela estreita e o fluxo completo no
  navegador são verificados pelo quickstart.
- **Credenciais legíveis pela interface** (Clarifications): as credenciais ficam num armazenamento
  do navegador que o código da própria página consegue ler. Se um código malicioso rodasse na
  página, poderia copiá-las. O risco é aceito porque o sistema roda na rede de casa, não carrega
  scripts nem recursos de terceiros (constituição, Princípio I) e cada credencial de renovação
  vale uma única vez (spec 003). Guardar a credencial num cookie protegido mudaria a API e exigiria
  proteção contra falsificação de requisições; não entra nesta spec.
- **Computador compartilhado** (Clarifications): como a sessão sobrevive ao fechar o navegador,
  quem usa um computador de outras pessoas deve escolher "Sair" ao terminar. Não há opção
  "manter conectado" nesta spec.
