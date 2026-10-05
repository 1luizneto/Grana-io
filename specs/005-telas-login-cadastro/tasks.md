---

description: "Lista de tarefas da feature 005-telas-login-cadastro (US-26 + critérios de tela da US-02)"
---

# Tasks: Telas de Login e Cadastro

**Input**: documentos de design em `/specs/005-telas-login-cadastro/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/interface.md](contracts/interface.md),
[quickstart.md](quickstart.md)

**Tests**: **obrigatórios** para a lógica de sessão e a exibição dos erros por campo (FR-020;
Clarifications Q3; Princípio IV). Escreva os testes primeiro e confirme que falham. O visual, a
tela estreita e o fluxo completo no navegador são validados pelo [quickstart.md](quickstart.md).

**Organization**: cada fase termina num **Checkpoint**. No checkpoint, pare com as suítes verdes,
apresente o resumo, faça o commit com a mensagem sugerida e o push (sem trailers de IA). PR e
merge ficam com o responsável.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**:
  - US1: entrar pela tela de login
  - US2: ficar conectado e proteger as páginas
  - US3: criar conta pela tela de cadastro
  - US4: sair do sistema
  - US5: layout base
- Suíte completa (constituição, Princípio IV): `sh testar.sh`, que roda as duas abaixo e falha
  se qualquer uma falhar. Interface: `docker compose run --rm frontend npm test`. Backend:
  `docker compose run --rm backend pytest` (163, sem mudança esperada).
- Caminhos relativos a `frontend/` quando começam com `src/`.

---

## Phase 1: Setup

**Purpose**: dependências novas, ambiente de testes da interface e imagem reconstruída.

- [X] T001 Instalar `react-router@8.4.0` como dependência de produção, com versão exata, rodando o `npm install` no container com `frontend/package.json` e `frontend/package-lock.json` montados ([research R-08](research.md)):
  `docker compose run --rm --no-deps -v ./frontend/package.json:/app/package.json -v ./frontend/package-lock.json:/app/package-lock.json frontend npm install --save-exact react-router@8.4.0`
- [X] T002 Instalar, do mesmo jeito, as dependências de desenvolvimento com versão exata (`--save-dev --save-exact`): `vitest@5.0.3`, `jsdom@30.1.2`, `@testing-library/react@16.3.3`, `@testing-library/user-event@14.6.7`, `@testing-library/jest-dom@7.0.1` ([research R-07](research.md)). Acrescentar ao `frontend/package.json` o script `"test": "vitest run"`
- [X] T003 Em `frontend/vite.config.js`, acrescentar o bloco `test: { environment: 'jsdom', setupFiles: ['./src/testes/preparacao.js'], restoreMocks: true }`. Criar `frontend/src/testes/preparacao.js`: importa `@testing-library/jest-dom/vitest`; `afterEach` com `cleanup()` do Testing Library e `localStorage.clear()`
- [X] T004 Criar `frontend/src/testes/ambiente.test.js` com 3 testes do próprio ambiente: o `localStorage` grava e lê; `AbortSignal.timeout` existe (ponto de atenção 3 do plano: se não existir no jsdom, registrar aqui e isolar a criação do sinal no `client.js` na T010); `globalThis.fetch` pode ser substituído por `vi.fn()`
- [X] T005 Criar `testar.sh` na raiz do repositório (`#!/bin/sh`, `set -e`): roda `docker compose run --rm backend pytest` e depois `docker compose run --rm frontend npm test`, termina com erro se qualquer uma falhar e imprime no fim "Backend e interface: todos os testes passaram." (constituição, Princípio IV; RNF-05: "rodar toda a suíte com um comando"). Reconstruir e validar: `docker compose up -d --build --wait`; `sh testar.sh` verde (163 do backend + T004); `http://localhost:5173` continua mostrando a página atual

  > **Resultado (2026-10-05)**: ✅ `sh testar.sh` verde: 163 do backend + 3 da interface.
  > - Instalação pelo container com `package.json` e `package-lock.json` montados (R-08); no Git
  >   Bash foi preciso `MSYS_NO_PATHCONV=1` e caminho absoluto (`$(pwd)/frontend/...`) nos `-v`.
  > - Ponto de atenção 3: o `AbortSignal.timeout` existe no jsdom 30; o `client.js` não precisa
  >   isolar a criação do sinal.
  > - `docker compose up -d --build --wait`: os três containers saudáveis; a interface responde 200.

**Checkpoint**: dependências instaladas na imagem, suíte da interface rodando no Docker.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: armazenamento da sessão, interpretação de erros, cliente autenticado com renovação
única, funções da API, rotas e provider base. Todas as histórias dependem disto.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T006 [P] Escrever **primeiro** `frontend/src/auth/armazenamento.test.js` ([data-model.md](data-model.md)):
  - `salvarSessao(s)` e `lerSessao()` devolvem o mesmo objeto, gravado na chave `grana.sessao`;
  - `apagarSessao()` remove a chave;
  - `lerSessao()` devolve `null` sem nada guardado;
  - JSON inválido, ou sem `acesso`, `renovacao` ou `usuario.nome` como textos não vazios → `null` **e** a chave é apagada;
  - nenhuma função guarda campo `senha`, mesmo se o objeto recebido tiver um (só `acesso`, `renovacao` e `usuario: {nome, email}` são gravados).
- [X] T007 [P] Escrever **primeiro** `frontend/src/api/erros.test.js` para `interpretarErro` ([research R-06](research.md)):
  - resposta 400 `{"email": ["a"], "senha": ["b", "c"]}` → `{campos: {email: ["a"], senha: ["b", "c"]}, geral: null}`;
  - 400 com `non_field_errors` → vai para `geral` (mensagens unidas por espaço);
  - 401/403/429 com `detail` → `geral` igual ao `detail`;
  - erro de rede (`TypeError`) e tempo esgotado (`DOMException` `TimeoutError`/`AbortError`) → `geral = "Não foi possível falar com o servidor. Tente novamente."`;
  - 500 ou corpo que não é JSON → a mesma mensagem genérica.
- [X] T008 [P] Escrever **primeiro** `frontend/src/api/client.test.js` para `requisitarAutenticada` ([research R-03](research.md)), com `fetch` simulado e sessão gravada:
  - envia `Authorization: Bearer <acesso>`;
  - 401 `{"code": "token_not_valid"}` → chama `POST /api/auth/renovar/` com a `renovacao`, grava o par novo e repete a requisição com o `acesso` novo, devolvendo a resposta da repetição;
  - **3 requisições simultâneas** com 401 `token_not_valid` → **1** chamada de renovação e 3 repetições com o acesso novo;
  - renovação respondendo 401 → sessão apagada, o callback registrado com `registrarAoExpirar(fn)` é chamado uma vez, e a função rejeita com um erro `SessaoExpirada`;
  - 401 sem `code` e 401 com `code: "user_inactive"` → mesmo tratamento de sessão expirada, sem tentar renovar;
  - sem sessão guardada → `SessaoExpirada` sem chamar o `fetch`;
  - **corrida entre abas**: a renovação responde 401, mas a sessão guardada já tem outra `renovacao` e outro `acesso` (simular gravando a sessão nova dentro do mock da renovação) → a requisição é repetida com o `acesso` guardado, a sessão **não** é apagada e o callback de expiração **não** é chamado ([research R-03](research.md), passo 4).

  Rodar a suíte e confirmar a **falha** de T006, T007 e T008.
- [X] T009 [P] Implementar `frontend/src/auth/armazenamento.js` (`lerSessao`, `salvarSessao`, `apagarSessao`; chave `grana.sessao`). Confirmar T006 **verde**
- [X] T010 [P] Implementar `frontend/src/api/erros.js` (`interpretarErro(respostaOuErro)`, assíncrona, e a constante `MENSAGEM_FALHA_COMUNICACAO`). Confirmar T007 **verde**
- [X] T011 Estender `frontend/src/api/client.js`, mantendo o `requisitar` público: `requisitarAutenticada(caminho, opcoes)`, `registrarAoExpirar(fn)` e a classe `SessaoExpirada`. Renovação única com uma variável de módulo que guarda a promessa em andamento e é zerada no `finally`. Com a renovação recusada, reler a sessão guardada antes de expirar (corrida entre abas, R-03 passo 4). Exportar `_reiniciarParaTestes()` para zerar o estado entre testes. Confirmar T008 **verde**
- [X] T012 [P] Criar `frontend/src/api/sessao.js` (`entrar(email, senha)`, `renovar(renovacao)`, `sair(renovacao)` via `requisitarAutenticada`, `obterEu()` via `requisitarAutenticada`) e `frontend/src/api/usuarios.js` (`cadastrar({nome, email, senha, confirmacao_senha})`), seguindo os contratos [api-sessao.md](../003-login-logout/contracts/api-sessao.md) e [api-cadastro.md](../002-cadastro-usuario/contracts/api-cadastro.md). Cada função devolve a `Response`; quem chama usa `interpretarErro` nas falhas
- [X] T013 [P] Criar os componentes de apresentação ([contracts/interface.md](contracts/interface.md), "Acessibilidade"):
  - `frontend/src/components/CampoTexto.jsx`: props `rotulo`, `nome`, `tipo`, `valor`, `aoMudar`, `erros` (lista), `autoComplete`; `<label htmlFor>` visível; com erros, `aria-invalid="true"` e `aria-describedby` apontando para a lista de mensagens logo abaixo do campo;
  - `frontend/src/components/AvisoFormulario.jsx`: mensagem geral com `role="alert"` (variante "erro" e "informação").
- [X] T014 Criar a base do `frontend/src/auth/AuthProvider.jsx`: contexto, hook `useAuth()`, estado inicial lido do `armazenamento` (`usuario` ou `null`; `estado` `"conectado"`/`"desconectado"`), `aviso` com `consumirAviso()`, e o registro de `registrarAoExpirar` que apaga a sessão, define `estado = "desconectado"` e o aviso "Sua sessão expirou. Entre novamente." (FR-008). As ações `entrar`, `cadastrarEEntrar` e `sair` entram nas histórias
- [X] T015 Criar `frontend/src/estilos.css` ([research R-10](research.md)): variáveis de cor, fonte do sistema, formulários em coluna com largura máxima de 420 px e campos 100%, botões com estado desabilitado, mensagens de erro em vermelho abaixo do campo, sem largura fixa maior que a tela. Em `frontend/src/main.jsx`, envolver o `App` com `<BrowserRouter>` e `<AuthProvider>`, e importar `estilos.css`. Em `frontend/src/App.jsx`, trocar o `<Inicio />` direto por `<Routes>` com `/` → `Inicio` (provisório, sem proteção até a US2). Criar `frontend/src/testes/renderizar.jsx` com `renderizarComRotas(ui, {rota = "/", rotas})`, que monta `MemoryRouter` + `AuthProvider`
- [X] T016 Rodar as duas suítes e abrir `http://localhost:5173`: a página atual continua aparecendo (agora via roteador)

  > **Resultado (2026-10-05)**: ✅ interface com 31 testes verdes (3 + 9 + 11 + 8); backend sem
  > mudança.
  > - T006 a T008 falharam primeiro (módulos inexistentes).
  > - Renovação única provada com 3 requisições simultâneas (1 chamada a `/auth/renovar/`, 3
  >   repetições) e a corrida entre abas (usa o par gravado pela outra aba, sem expirar).
  > - Ajustes de desenho: a função de renovação ficou **dentro do `client.js`** (não em
  >   `api/sessao.js`), para evitar importação circular e manter a renovação única num lugar só.
  >   No `AuthProvider`, o aviso é exposto como `aviso` + `limparAviso()` (em vez de
  >   `consumirAviso()`, que mudaria estado durante a renderização).
  > - O `requisitar` passou a mesclar os cabeçalhos (`Accept` + os da chamada), em vez de
  >   substituí-los; a saúde (spec 001) continua igual.
  > - T016: `http://localhost:5173/` mostra "Grana.io" e "API acessível (banco operacional)" pelo
  >   roteador, sem erros no console.

**Checkpoint**: base de sessão, cliente com renovação única e roteador prontos; suítes verdes.

---

## Phase 3: User Story 1 - Entrar pela tela de login (Priority: P1) 🎯 MVP

**Goal**: a pessoa entra por `/entrar` e chega à página inicial com o nome no cabeçalho provisório.

**Independent Test**: quickstart S3.

### Tests for User Story 1 ⚠️

- [X] T017 [P] [US1] Escrever `frontend/src/auth/AuthProvider.test.jsx` (parte de `entrar`): com `fetch` simulado, `entrar("ana@exemplo.com", "x")` com 200 grava a sessão (`acesso`, `renovacao`, `usuario`), põe `estado = "conectado"` e expõe o `usuario`; com 401 devolve `{ok: false, erro}` com `geral = "E-mail ou senha incorretos."` e não grava nada
- [X] T018 [P] [US1] Escrever `frontend/src/pages/Entrar/Entrar.test.jsx` (Testing Library + `user-event`, `fetch` simulado):
  - envio vazio com 400 da API → "Este campo é obrigatório." abaixo de "E-mail" e de "Senha" (mensagem ligada ao campo por `aria-describedby`);
  - 401 → "E-mail ou senha incorretos." num `role="alert"`, e-mail mantido, senha vazia;
  - 429 → "Muitas tentativas. Tente novamente em instantes.";
  - falha de rede → "Não foi possível falar com o servidor. Tente novamente.", e-mail mantido;
  - durante o envio, o botão mostra "Entrando…" e fica desabilitado (FR-005);
  - 200 → navega para `/` (rota de teste que mostra "início");
  - Enter no campo de senha envia o formulário.

  Rodar e confirmar a **falha**.

### Implementation for User Story 1

- [X] T019 [US1] Acrescentar `entrar(email, senha)` ao `AuthProvider.jsx`: chama `api/sessao.entrar`; com 200 grava a sessão e atualiza o estado; senão devolve `{ok: false, erro: await interpretarErro(resposta)}`; erros de rede viram o mesmo formato. A senha nunca é guardada (FR-016)
- [X] T020 [US1] Implementar `frontend/src/pages/Entrar/Entrar.jsx`: título "Entrar", campos "E-mail" (`type="email"`, `autoComplete="username"`) e "Senha" (`type="password"`, `autoComplete="current-password"`), botão "Entrar"/"Entrando…", link "Criar conta" para `/cadastro`, `AvisoFormulario` para o erro geral. Depois de recusa, apaga a senha e mantém o e-mail (FR-004). Com sucesso, `navigate("/", {replace: true})` (o retorno à página pedida entra na US2)
- [X] T021 [US1] Em `frontend/src/App.jsx`, acrescentar a rota `/entrar`. Em `frontend/src/pages/Inicio/Inicio.jsx`, mostrar "Olá, {usuario.nome}!" e o aviso "Os recursos financeiros chegam nas próximas entregas." (FR-017), mantendo por enquanto o estado da API logo abaixo. Até a proteção da US2 (T028), a rota `/` fica aberta: sem `usuario`, a página mostra só o aviso, sem saudação e sem quebrar. Rodar as suítes e confirmar T017 e T018 **verdes**
- [X] T022 [US1] Validar o S3 do [quickstart.md](quickstart.md) no navegador. Nesta fase o nome aparece na saudação da página inicial; o nome no cabeçalho (US1, cenário 1) só existe a partir da T038 e é conferido no S8 e no S9

  > **Resultado (2026-10-05)**: ✅ interface com 40 testes verdes (31 + 2 do provider + 7 da tela).
  > - T017 e T018 falharam primeiro (`entrar` e a tela inexistentes).
  > - S3 no navegador: senha errada → "E-mail ou senha incorretos.", e-mail mantido, senha vazia;
  >   dados certos → `/` com "Olá, Ana Souza!"; a sessão gravada não contém a senha.
  > - **Achado**: com os campos em branco, a API responde "Este campo pode não estar em branco."
  >   (texto padrão do DRF para campo vazio), e não "Este campo é obrigatório." como a spec (US1,
  >   cenário 3) e o contrato da spec 003 citam (esse texto é o de campo **ausente**). A interface
  >   mostra o texto da API como está (Princípio V). Decisão pendente com o responsável antes da US2.
  > - `testes/preparacao.js` passou a desfazer os `fetch` simulados e o estado do cliente entre os
  >   testes; `testes/respostas.js` reúne as respostas simuladas.

**Checkpoint**: login funcionando pela tela; suítes verdes.

---

## Phase 4: User Story 2 - Ficar conectado e proteger as páginas (Priority: P1)

**Goal**: sessão persiste em recarga e ao reabrir; páginas protegidas levam ao login e voltam para a
página pedida; renovação transparente; sessão expirada leva ao login com aviso.

**Independent Test**: quickstart S2, S4, S5 e S6.

### Tests for User Story 2 ⚠️

- [ ] T023 [P] [US2] Escrever `frontend/src/auth/rotas.test.jsx` ([research R-05](research.md)):
  - sem sessão, abrir `/` → mostra a tela de login e não mostra o conteúdo protegido;
  - sem sessão, abrir `/algum-lugar-protegido`, entrar com sucesso → volta para `/algum-lugar-protegido`;
  - com sessão, abrir `/entrar` ou `/cadastro` → vai para `/` (FR-010);
  - com `estado = "verificando"`, a rota protegida mostra "Carregando…" e nenhum conteúdo protegido (SC-004).
- [ ] T024 [P] [US2] Acrescentar a `frontend/src/auth/AuthProvider.test.jsx`:
  - com sessão guardada, ao montar fica `"verificando"`, chama `GET /api/usuarios/eu/` uma vez e passa a `"conectado"`, atualizando o nome com o da resposta;
  - montado duas vezes em `StrictMode`, com o acesso vencido (401 `token_not_valid`), a renovação é chamada **uma** vez e a sessão continua (ponto de atenção 2 do plano);
  - com renovação recusada, termina `"desconectado"`, sessão apagada e aviso "Sua sessão expirou. Entre novamente.";
  - sem sessão guardada, não chama a API e fica `"desconectado"`;
  - com sessão guardada e **falha de rede** na verificação, fica `"conectado"` com o nome guardado e a sessão não é apagada ([research R-04](research.md)).
- [ ] T025 [P] [US2] Acrescentar a `frontend/src/pages/Entrar/Entrar.test.jsx`: com um aviso pendente no provider, a tela mostra "Sua sessão expirou. Entre novamente." uma vez (o aviso é consumido).

  Rodar e confirmar a **falha**.

### Implementation for User Story 2

- [ ] T026 [US2] Acrescentar a verificação inicial ao `AuthProvider.jsx`: com sessão guardada, `estado = "verificando"` e chamada a `obterEu()`; 200 atualiza `usuario` (e grava); `SessaoExpirada` já é tratada pelo callback da T014; erro de rede mantém a sessão e marca `"conectado"` com o nome guardado (sem derrubar a pessoa por queda momentânea do servidor)
- [ ] T027 [US2] Implementar `frontend/src/auth/RotaProtegida.jsx` e `frontend/src/auth/RotaPublica.jsx` conforme [research R-05](research.md) (`<Navigate replace state={{de: location}}>` e "Carregando…")
- [ ] T028 [US2] Em `frontend/src/App.jsx`, colocar `/` atrás de `RotaProtegida` (como rota-pai, para que as próximas telas entrem como filhas) e `/entrar` atrás de `RotaPublica`. Em `Entrar.jsx`, depois do sucesso, navegar para `location.state?.de?.pathname ?? "/"` com `replace`, e mostrar o aviso do provider (consumindo-o) num `AvisoFormulario` de informação. Rodar as suítes e confirmar T023 a T025 **verdes**
- [ ] T029 [US2] Validar S2, S4, S5 e S6 do [quickstart.md](quickstart.md). No S6, conferir nos logs do backend **um único** `POST /api/auth/renovar/` por recarga

**Checkpoint**: sessão persistente, páginas protegidas e renovação transparente; suítes verdes.

---

## Phase 5: User Story 3 - Criar conta pela tela de cadastro (Priority: P1)

**Goal**: cadastro pela tela, erros por campo todos de uma vez, entrada automática depois do
cadastro (FR-019).

**Independent Test**: quickstart S7.

### Tests for User Story 3 ⚠️

- [ ] T030 [P] [US3] Acrescentar a `frontend/src/auth/AuthProvider.test.jsx` (parte de `cadastrarEEntrar`):
  - 201 no cadastro e 200 no login → sessão gravada, `"conectado"`, `{ok: true}`;
  - 400 no cadastro → `{ok: false, erro}` com os erros por campo, sem chamar o login;
  - 201 no cadastro e falha no login → `{ok: false, contaCriada: true, email}` e nada gravado.
- [ ] T031 [P] [US3] Escrever `frontend/src/pages/Cadastro/Cadastro.test.jsx`:
  - 400 com `email`, `senha` e `confirmacao_senha` → as três mensagens aparecem ao mesmo tempo, cada uma abaixo do seu campo; nome e e-mail mantidos; senha e confirmação vazias (SC-006, FR-004);
  - 403 → "O cadastro de novas contas está desativado neste sistema." acima do formulário;
  - sucesso completo → navega para `/`;
  - conta criada e login falho → navega para `/entrar` com o e-mail preenchido e o aviso "Conta criada. Entre com sua senha.";
  - o link "Já tenho conta" leva a `/entrar`, e o botão mostra "Criando conta…" durante o envio.

  Rodar e confirmar a **falha**.

### Implementation for User Story 3

- [ ] T032 [US3] Acrescentar `cadastrarEEntrar({nome, email, senha, confirmacao_senha})` ao `AuthProvider.jsx` ([research R-04](research.md)); no caso "conta criada, login falhou", definir o aviso "Conta criada. Entre com sua senha."
- [ ] T033 [US3] Implementar `frontend/src/pages/Cadastro/Cadastro.jsx` com "Nome" (`autoComplete="name"`), "E-mail" (`autoComplete="email"`), "Senha" e "Confirme a senha" (`autoComplete="new-password"`), botão "Criar conta"/"Criando conta…" e link "Já tenho conta". Ao cair no caso "conta criada", navegar para `/entrar` com `state: {email}`. Em `Entrar.jsx`, usar `location.state?.email` como valor inicial do e-mail
- [ ] T034 [US3] Em `frontend/src/App.jsx`, acrescentar `/cadastro` atrás de `RotaPublica`. Rodar as suítes e confirmar T030 e T031 **verdes**. Validar o S7 do [quickstart.md](quickstart.md)

**Checkpoint**: cadastro pela tela com entrada automática; suítes verdes.

---

## Phase 6: User Story 4 - Sair do sistema (Priority: P2)

**Goal**: "Sair" encerra a sessão no servidor, sempre descarta a local e leva ao login com aviso.

**Independent Test**: quickstart S8.

### Tests for User Story 4 ⚠️

- [ ] T035 [P] [US4] Acrescentar a `frontend/src/auth/AuthProvider.test.jsx` (parte de `sair`):
  - chama `POST /api/auth/sair/` com `{"renovacao": ...}` e `Authorization`;
  - com 204, com 400 e com **falha de rede**: a sessão é apagada, `estado = "desconectado"` e o aviso é "Você saiu do sistema." (FR-011).
- [ ] T036 [P] [US4] Escrever `frontend/src/components/Layout.test.jsx`: conectada, o cabeçalho mostra "Grana.io", o nome da pessoa e o botão "Sair"; clicar em "Sair" leva a `/entrar` com "Você saiu do sistema."; depois disso, voltar para `/` (navegação simulada) mostra o login de novo.

  Rodar e confirmar a **falha**.

### Implementation for User Story 4

- [ ] T037 [US4] Acrescentar `sair()` ao `AuthProvider.jsx`, com a limpeza local no `finally`
- [ ] T038 [US4] Implementar `frontend/src/components/Layout.jsx` com o cabeçalho (`<header>`: "Grana.io", nome, botão "Sair" que chama `sair()` e navega para `/entrar` com `replace`) e `<main><Outlet /></main>`. Em `App.jsx`, usar o `Layout` como elemento da rota-pai protegida. Rodar as suítes e confirmar T035 e T036 **verdes**. Validar o S8 do [quickstart.md](quickstart.md)

**Checkpoint**: saída funcionando, inclusive sem servidor; suítes verdes.

---

## Phase 7: User Story 5 - Layout base da aplicação (Priority: P2)

**Goal**: menu, rodapé com o estado da API em todas as telas, página não encontrada e tela estreita.

**Independent Test**: quickstart S9 e S10.

### Tests for User Story 5 ⚠️

- [ ] T039 [P] [US5] Acrescentar a `frontend/src/components/Layout.test.jsx`: o menu (`<nav>`) tem o link "Início" para `/`; as telas de login e cadastro não mostram o menu nem o botão "Sair".
- [ ] T040 [P] [US5] Escrever `frontend/src/pages/NaoEncontrada/NaoEncontrada.test.jsx`: um endereço inexistente mostra "Página não encontrada." e o link "Voltar ao início" para `/`, com ou sem sessão.

  Rodar e confirmar a **falha**.

### Implementation for User Story 5

- [ ] T041 [US5] Acrescentar o menu ao `Layout.jsx` (`<nav aria-label="Menu principal">` com `NavLink` "Início"; marca o item atual com `aria-current`)
- [ ] T042 [US5] Criar `frontend/src/components/Rodape.jsx` com o estado da API (`useSaudeApi` e as mensagens que hoje estão em `Inicio.jsx`) e exibi-lo em todas as telas, fora das rotas (no `App.jsx`, depois de `<Routes>`), para rodar uma vez por carregamento. Tirar o estado da API de `Inicio.jsx` ([research R-09](research.md))
- [ ] T043 [US5] Implementar `frontend/src/pages/NaoEncontrada/NaoEncontrada.jsx` e a rota `*` no `App.jsx`. Rodar as suítes e confirmar T039 e T040 **verdes**
- [ ] T044 [US5] Ajustar `frontend/src/estilos.css` para o layout: cabeçalho e menu que quebram em coluna abaixo de 640 px, rodapé discreto. Validar S9 e S10 do [quickstart.md](quickstart.md) (360 px sem rolagem horizontal; só teclado; banco parado mostrado no rodapé)

**Checkpoint**: layout base completo; suítes verdes.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T045 [P] Atualizar o `README.md`:
  - "Estado atual": a interface tem login, cadastro e o layout base;
  - seção 6: `sh testar.sh` como comando principal (as duas suítes), e os comandos de cada camada separados;
  - seção 3: as telas `/entrar` e `/cadastro`, e o aviso de que a sessão fica no navegador até sair (computador compartilhado: usar "Sair");
  - nota para quem desenvolve: depois de mudar `package.json` ou `vite.config.js`, `docker compose up -d --build frontend`, e como instalar dependências ([research R-08](research.md)).
- [ ] T046 [P] Atualizar `specs/001-infra-docker/quickstart.md`, passos que citam "a página exibe ... a API": o estado da API agora aparece no rodapé, inclusive na tela de login
- [ ] T047 Executar o [quickstart.md](quickstart.md) completo (S1 a S10) e registrar o resultado, incluindo os tempos do S3 e do S7 (SC-001, SC-002), as duas abas do S8 e a verificação de recursos de terceiros do S10 (FR-016)
- [ ] T048 Fechar a Definition of Done:
  - suítes verdes e todas as tarefas marcadas;
  - em `BACKLOG.md`, marcar ☑ os 4 critérios da US-26 e, na US-02, os 2 critérios de tela ("O logout invalida a sessão no frontend e redireciona para o login" e "Rotas protegidas redirecionam para o login quando não há sessão"), com nota "spec 005".

**Checkpoint**: feature pronta para PR na `main`; Sprint 1 completa.

---

## Dependencies & Execution Order

```text
Setup → Foundational → US1 → US2 → US3 → US4 → US5 → Polish
```

- **Foundational** bloqueia tudo (armazenamento, cliente, provider base, roteador).
- **US1** cria a tela de login, que a US2 usa para provar o retorno à página pedida.
- **US2** cria `RotaProtegida`/`RotaPublica`, usadas pela US3 (cadastro) e pela US4 (layout
  protegido).
- **US4** cria o `Layout` com o cabeçalho; **US5** completa menu, rodapé e "não encontrada".
- `AuthProvider.jsx`, `AuthProvider.test.jsx`, `App.jsx`, `Entrar.jsx`, `Layout.jsx` e
  `estilos.css` são editados por várias fases, sempre em sequência.

### Parallel Opportunities

- Foundational: T006 ∥ T007 ∥ T008 (testes); T009 ∥ T010; T012 ∥ T013.
- US1: T017 ∥ T018. US2: T023 ∥ T024 ∥ T025. US3: T030 ∥ T031. US4: T035 ∥ T036. US5: T039 ∥ T040.
- Polish: T045 ∥ T046.

## Parallel Example: Foundational

```bash
Task: "T006 Testes do armazenamento em frontend/src/auth/armazenamento.test.js"
Task: "T007 Testes de interpretarErro em frontend/src/api/erros.test.js"
Task: "T008 Testes do cliente autenticado em frontend/src/api/client.test.js"
```

## Implementation Strategy

### MVP First

Setup + Foundational + US1 + US2 + US3: entrar, ficar conectado, páginas protegidas e criar conta
pelo navegador. Com isso a pessoa usa o sistema sem comandos. Sair (US4) e o layout completo (US5)
fecham a US-26 e os critérios de tela da US-02.

### Incremental Delivery

Um checkpoint por fase, com as duas suítes verdes e o cenário do quickstart da fase validado no
navegador.

## Notes

- **Rebuild do frontend** depois de T001 a T003 (dependências e `vite.config.js` ficam na imagem).
- **Renovação única** é requisito de correção, não otimização (spec 003: uso único). O teste de 3
  requisições simultâneas (T008) e o de `StrictMode` (T024) são obrigatórios.
- **Nada de recurso externo** (FR-016): sem CDN, fontes ou ícones de terceiros.
- Commits em pt-BR, Conventional Commits, **sem** `Co-Authored-By` nem rodapés de IA; push a cada
  commit (constituição v1.2.0). PR e merge são do responsável.

**Commit recomendado após cada checkpoint (T005, T016, T022, T029, T034, T038, T044, T048)**:

| Checkpoint | Mensagem sugerida |
|---|---|
| T005 | `chore: adiciona react-router e ambiente de testes da interface` |
| T016 | `feat: adiciona cliente autenticado com renovação única e base da sessão` |
| T022 | `feat: adiciona tela de login (US1)` |
| T029 | `feat: protege as páginas e mantém a sessão ao recarregar (US2)` |
| T034 | `feat: adiciona tela de cadastro com entrada automática (US3)` |
| T038 | `feat: adiciona saída pelo cabeçalho (US4)` |
| T044 | `feat: completa o layout base com menu, rodapé e página não encontrada (US5)` |
| T048 | `docs: documenta as telas de acesso e conclui US-26` |

O primeiro commit (T005) também inclui os artefatos da spec (`specs/005-telas-login-cadastro/`) e
o `testar.sh`.
