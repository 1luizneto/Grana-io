# Research: Telas de Login e Cadastro

**Feature**: `005-telas-login-cadastro` | **Plano**: [plan.md](plan.md)

Decisões técnicas da primeira spec de interface. Seguem o `docs/arquitetura.md` §3 (Provider,
hooks, cliente de API centralizado, `RotaProtegida`, páginas × componentes) e a constituição
(Princípio V: a interface só exibe o que a API devolve).

Versões conferidas em 2026-10-05 com `npm view` no container do frontend (Node 24.21).

---

## R-01 — Navegação: `react-router` 8.4.0 (dependência nova)

**Decisão**: `react-router` 8.4.0 (o pacote único, que substituiu o `react-router-dom`) no modo
declarativo: `<BrowserRouter>`, `<Routes>`, `<Route>`, `<Navigate>`, `useNavigate`,
`useLocation`. Rotas em pt-BR (`docs/arquitetura.md` §4):

| Rota | Página | Acesso |
|---|---|---|
| `/entrar` | Login | só sem sessão (com sessão → `/`) |
| `/cadastro` | Cadastro | só sem sessão (com sessão → `/`) |
| `/` | Início (dentro do layout) | exige sessão |
| `*` | Página não encontrada | livre |

**Rationale**: a spec exige endereços próprios por página, "voltar" do navegador, retorno à página
pedida depois do login (FR-009) e página não encontrada (FR-018). É o roteador de fato do React,
sem dependências próprias, e o Vite já serve `index.html` para qualquer caminho no modo dev
(fallback de SPA), então `/entrar` aberto direto funciona.

**Alternativas consideradas**:
- *Roteamento feito à mão com `history.pushState`*: reinventaria histórico, links e redirecionamentos,
  com mais código para testar. Rejeitado (Princípio VI: a dependência evita complexidade).
- *Modo "framework" do React Router (loaders, SSR)*: exige reorganizar o projeto e o build. YAGNI.

---

## R-02 — Onde a sessão fica: `localStorage`, chave `grana.sessao`

**Decisão**: a sessão (`acesso`, `renovacao`, `usuario: {nome, email}`) fica em JSON no
`localStorage`, chave `grana.sessao`, num módulo único `src/auth/armazenamento.js` (`lerSessao`,
`salvarSessao`, `apagarSessao`). JSON inválido ou incompleto é tratado como "sem sessão" e
apagado.

**Rationale**: a Q2 da clarificação decidiu que a sessão sobrevive a fechar o navegador, o que
descarta o `sessionStorage`; a Q4 aceitou o armazenamento legível pela interface, sem mudar a API.
Um módulo único facilita os testes e uma troca futura (ex.: cookie no RNF-09).

**Alternativas consideradas**: `sessionStorage` (contraria a Q2); IndexedDB (assíncrono, sem
ganho de segurança); cookie protegido (rejeitado na Q4).

---

## R-03 — Cliente de API com renovação única

**Decisão**: o `src/api/client.js` ganha `requisitarAutenticada(caminho, opcoes)`, além do
`requisitar` público que já existe:

1. lê a sessão e envia `Authorization: Bearer <acesso>`;
2. se a resposta for 401 com `code == "token_not_valid"`, chama a renovação e repete a
   requisição **uma vez** com a credencial nova;
3. a renovação é **única por vez**: uma variável de módulo guarda a promessa da renovação em
   andamento, e as requisições que chegam enquanto ela existe esperam a mesma promessa
   (FR-007; edge case "várias requisições ao mesmo tempo");
4. se a renovação responder 401 ou 400, o cliente **relê a sessão guardada** antes de desistir:
   se a credencial de renovação guardada já é outra (outra aba renovou primeiro, e a renovação é
   de uso único), repete a requisição com o `acesso` guardado, sem expirar a sessão;
5. se a sessão guardada continua a mesma, ou se o 401 vier sem `code`, ou com
   `code == "user_inactive"`, a sessão é apagada e o cliente chama o aviso de sessão expirada
   registrado pelo `AuthProvider` (FR-008);
6. o par novo devolvido pela renovação é salvo antes de repetir a requisição.

A renovação única do passo 3 vale dentro de uma aba; o passo 4 cobre a corrida entre abas, que
compartilham o mesmo `localStorage` (edge case "várias abas abertas").

O comportamento segue a "Regra para a interface (US-26)" do contrato da spec 003
([api-sessao.md](../003-login-logout/contracts/api-sessao.md)).

**Rationale**: concentrar a regra num lugar só (`docs/arquitetura.md` §3, Adapter) e testá-la
isolada. A renovação única é obrigatória, não um detalhe: cada credencial de renovação vale uma
vez, e duas renovações paralelas fariam a segunda falhar e derrubar a sessão. O `StrictMode` do
React, que executa efeitos duas vezes em desenvolvimento, provoca exatamente esse caso.

**Alternativas consideradas**: renovar antes de vencer, com temporizador (mais estado, e ainda
precisa tratar o 401); interceptadores de uma biblioteca HTTP (dependência sem necessidade).

---

## R-04 — Sessão na interface: `AuthProvider` + `useAuth`

**Decisão**: `src/auth/AuthProvider.jsx` (Context) expõe, via `useAuth()`:

- `usuario` (nome e e-mail ou `null`) e `estado` (`"verificando" | "conectado" | "desconectado"`);
- `entrar(email, senha)`, `cadastrarEEntrar(dados)` e `sair()`;
- `aviso` de uma vez só (ex.: "Sua sessão expirou. Entre novamente."), que a tela de login mostra.

Na abertura do app, se houver sessão guardada, o provider fica em `"verificando"` e consulta
`GET /api/usuarios/eu/` pelo cliente autenticado. Isso renova a credencial se preciso, confirma que
a sessão ainda vale (edge case "recarregar com a sessão vencida") e atualiza o nome. Enquanto
verifica, as rotas protegidas mostram "Carregando…" e nenhum dado (SC-004). Se a verificação
falhar **por rede** (servidor fora do ar), a sessão é mantida e a pessoa fica conectada com o nome
guardado: uma queda momentânea não pode desconectá-la. Só a recusa da renovação expira a sessão.

`sair()` chama `POST /api/auth/sair/` com a renovação e **sempre** apaga a sessão local no
`finally`, mesmo com erro de rede (FR-011, US4 cenário 4).

`cadastrarEEntrar` chama `POST /api/usuarios/`; com 201, chama `entrar` com o mesmo e-mail e senha
(FR-019). Se esse login falhar, devolve um resultado que leva ao login com o e-mail preenchido e o
aviso "Conta criada. Entre com sua senha."

**Rationale**: é o padrão já previsto no documento de arquitetura (Provider + hooks, sem Redux).

---

## R-05 — Guardas de rota: `RotaProtegida` e `RotaPublica`

**Decisão**: dois componentes em `src/auth/`:

- `RotaProtegida`: com `estado == "verificando"` mostra "Carregando…"; sem sessão, `<Navigate
  to="/entrar" replace state={{ de: location }} />`; com sessão, renderiza o filho (o layout);
- `RotaPublica` (login e cadastro): com sessão, `<Navigate to="/" replace />` (FR-010).

Depois do login, a tela volta para `state.de` (ou `/`), sempre com `replace`. Ao sair, a
navegação para `/entrar` também usa `replace`, e as páginas protegidas checam a sessão a cada
renderização, então o "voltar" do navegador cai de novo no login (SC-005).

---

## R-06 — Erros da API exibidos por campo

**Decisão**: `src/api/erros.js` com `interpretarErro(resposta | erro)`, que devolve
`{ campos: {nome: [mensagens]}, geral: "mensagem" | null }`:

- 400 do DRF → cada chave vira erro do campo; `non_field_errors` e `detail` viram `geral`;
- 401, 403 e 429 com `detail` → `geral` (ex.: "E-mail ou senha incorretos.", cadastro fechado,
  muitas tentativas);
- falha de rede ou tempo esgotado → `geral = "Não foi possível falar com o servidor. Tente
  novamente."` (FR-015);
- qualquer outra resposta → a mesma mensagem genérica de falha.

O componente `CampoTexto` mostra rótulo, campo e a lista de erros logo abaixo do campo, ligada por
`aria-describedby` e `aria-invalid` (FR-003, FR-014).

**Rationale**: as mensagens vêm da API sem tradução nem regra (Princípio V); a interface só decide
**onde** mostrar.

---

## R-07 — Testes da interface: Vitest + Testing Library (dependências de desenvolvimento)

**Decisão**: `vitest` 5.0.3, `jsdom` 30.1.2, `@testing-library/react` 16.3.3,
`@testing-library/user-event` 14.6.7 e `@testing-library/jest-dom` 7.0.1, todas em
`devDependencies` com versão exata. Configuração no próprio `vite.config.js` (bloco `test`:
`environment: "jsdom"`, `setupFiles`), script `"test": "vitest run"`. Os testes ficam ao lado do
código (`*.test.js(x)` em `src/`), porque só `src/` é montado no container.

Comando único no Docker (FR-020; constituição, Princípio IV):

```bash
docker compose run --rm frontend npm test
```

O `fetch` é simulado nos testes (`vi.fn` em `globalThis.fetch`), sem servidor de mock (MSW seria
mais uma dependência sem necessidade para o volume atual).

**Escopo testado** (Clarifications Q3): armazenamento, cliente com renovação única, interpretação
de erros, guardas de rota, `AuthProvider` (entrar, cadastrar e entrar, sair, sessão expirada) e as
telas de login e cadastro quanto a erros por campo, dados mantidos e redirecionamentos. O visual e
a tela estreita ficam no quickstart.

**Rationale**: Vitest usa a mesma configuração do Vite, sem Babel nem Jest; Testing Library testa
pelo que a pessoa vê (rótulos e textos).

**Alternativas consideradas**: Jest (configuração separada para JSX e ESM); Playwright/Cypress
(navegador real, imagem pesada; o fluxo completo fica no quickstart).

---

## R-08 — Instalar dependências sem `node_modules` no host

**Decisão**: o container do frontend só monta `src/`, e o `package.json` vive na imagem. Para
instalar e atualizar o `package-lock.json` no host, rodar o `npm install` no container montando os
dois arquivos:

```bash
docker compose run --rm --no-deps \
  -v ./frontend/package.json:/app/package.json \
  -v ./frontend/package-lock.json:/app/package-lock.json \
  frontend npm install --save-exact react-router@8.4.0
```

(e o equivalente com `--save-dev` para as de teste). Depois, `docker compose up -d --build
frontend` reconstrói a imagem com `npm ci`. O `vite.config.js` também fica na imagem, então mudar
o bloco `test` pede rebuild.

**Rationale**: mantém a decisão da spec 001 (só `src/` montado; `node_modules` dentro da imagem).

---

## R-09 — Indicador de saúde vai para o rodapé

**Decisão**: o aviso de saúde da API (`useSaudeApi`, spec 001) sai do conteúdo da página inicial e
vira um rodapé discreto, presente em todas as telas, inclusive login e cadastro.

**Rationale**: o quickstart da spec 001 (passos 2 e o de banco parado) espera ver o estado da API
ao abrir `http://localhost:5173`, que agora mostra o login. No rodapé, a verificação continua
valendo sem precisar entrar, e a página inicial fica com a saudação (FR-017).

---

## R-10 — Visual

**Decisão**: CSS simples num arquivo `src/estilos.css` (importado no `main.jsx`), com variáveis de
cor, layout em coluna única abaixo de 640 px, campos com largura 100% e sem largura fixa maior que
a tela (FR-013). Sem biblioteca de componentes nem de CSS e sem fontes externas (FR-016: nenhum
recurso de terceiros).

**Rationale**: o refinamento visual é do RNF-04; uma biblioteca de UI seria uma dependência grande
sem necessidade agora.

---

## Resumo de dependências novas

| Pacote | Versão | Tipo | Motivo |
|---|---|---|---|
| `react-router` | 8.4.0 | produção | rotas, redirecionamentos e "voltar" (R-01) |
| `vitest` | 5.0.3 | dev | executor de testes (R-07) |
| `jsdom` | 30.1.2 | dev | DOM simulado (R-07) |
| `@testing-library/react` | 16.3.3 | dev | renderizar e consultar componentes (R-07) |
| `@testing-library/user-event` | 14.6.7 | dev | digitação e cliques realistas (R-07) |
| `@testing-library/jest-dom` | 7.0.1 | dev | asserções de DOM (`toBeInTheDocument`) (R-07) |

Nenhuma muda o backend. Nenhuma é carregada de CDN: tudo é empacotado pelo Vite (FR-016).
