# Implementation Plan: Telas de Login e Cadastro

**Branch**: `005-telas-login-cadastro` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-telas-login-cadastro/spec.md`

**Backlog**: US-26, mais os dois critérios de tela da US-02 (sair redireciona ao login; rotas
protegidas redirecionam ao login).

## Summary

Primeira spec de interface. Entrega as telas de login e cadastro, a proteção das páginas, a
sessão que sobrevive a recargas e a fechar o navegador, a renovação automática e única da
credencial, a saída e o layout base (cabeçalho, menu, rodapé), sem mudar a API:

- **Rotas** com `react-router` 8.4 (`/entrar`, `/cadastro`, `/` e "não encontrada");
- **Sessão** no `localStorage` (`grana.sessao`), gerida pelo `AuthProvider` (`useAuth`) e
  verificada ao abrir com `GET /api/usuarios/eu/`;
- **Cliente de API** com `requisitarAutenticada`: Bearer, renovação única por vez e repetição;
  sessão expirada leva ao login com aviso;
- **Erros** da API mostrados por campo, sem tradução (Princípio V);
- **Testes** com Vitest + Testing Library para a lógica de sessão e os erros por campo, rodando
  com `docker compose run --rm frontend npm test`.

Detalhes em [research.md](research.md).

## Technical Context

**Language/Version**: JavaScript (ES2022+, JSX), React 19.3, Vite 8.3, Node 24 (container).
Backend sem mudanças (Python 3.12, Django 5.2, DRF 3.18).

**Primary Dependencies**: `react-router` 8.4.0 (nova, produção). Desenvolvimento: `vitest` 5.0.3,
`jsdom` 30.1.2, `@testing-library/react` 16.3.3, `@testing-library/user-event` 14.6.7,
`@testing-library/jest-dom` 7.0.1 ([R-07](research.md)).

**Storage**: `localStorage` do navegador, chave `grana.sessao` ([R-02](research.md);
[data-model.md](data-model.md)). Nada novo no PostgreSQL.

**Testing**: Vitest (ambiente jsdom) + Testing Library, `fetch` simulado. Suíte do backend
inalterada (163).

**Target Platform**: navegadores atuais (Chrome, Edge, Firefox) no PC e no celular da rede local.

**Project Type**: aplicação web. Esta spec mexe só no `frontend/`.

**Performance Goals**: entrar em até 30 s (SC-002) e cadastrar em até 2 min (SC-001), dominados
pela digitação; a renovação não pode ser percebida (FR-007).

**Constraints**:
- nenhuma regra de negócio na interface (Princípio V);
- nenhum recurso de terceiros (FR-016; Princípio I);
- renovação única por vez (uso único da credencial, spec 003);
- 360 px sem rolagem horizontal;
- `package.json` e `vite.config.js` ficam na imagem (rebuild ao mudar; [R-08](research.md)).

**Scale/Scope**: 4 rotas, 4 páginas, 1 provider, 2 guardas de rota, ~5 componentes de
apresentação, cliente de API estendido.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Princípio / regra | Avaliação pré-pesquisa | Pós-design |
|---|---|---|---|
| I | Localidade e privacidade | Nada sai da máquina; nenhuma CDN, fonte ou script externo. Senha nunca guardada. | ✅ Dependências empacotadas pelo Vite. Risco das credenciais legíveis aceito na clarificação Q4, condicionado a não haver terceiros (FR-016). |
| II | Isolamento por usuário | A interface só mostra o que a API devolve para a sessão atual. | ✅ Sem dados de domínio nesta spec. Sair apaga a sessão local (sem resto de outra pessoa no mesmo navegador). |
| III | Precisão monetária | N/A. | ✅ N/A |
| IV | Testes obrigatórios (test-first) | Autenticação é core. A Q3 incluiu testes da lógica de sessão e dos erros por campo, com um comando no Docker. | ✅ Vitest + Testing Library; testes escritos antes de cada módulo. `testar.sh` roda as duas suítes com um comando ("a suíte completa"). Visual no quickstart (S1 a S10). |
| V | Separação backend/frontend | Comunicação só pela API, URL configurável (`VITE_API_URL`), mensagens vindas da API. | ✅ [contracts/interface.md](contracts/interface.md) referencia os contratos 002 e 003 sem mudá-los. |
| VI | Simplicidade / incremental | US-26. Dependências novas precisam de justificativa. | ✅ Justificadas em R-01 e R-07 (tabela no fim do research). Sem Redux, sem biblioteca de UI, sem MSW. |
| — | Stack | "React (Vite), consumindo apenas a API REST do backend". | ✅ |
| — | `docs/arquitetura.md` §3 | `AuthProvider` (Context), `useAuth`, cliente centralizado com refresh automático e tradução de erros, `RotaProtegida`, páginas × componentes, estrutura `api/ auth/ hooks/ components/ pages/ utils/`. | ✅ Exatamente isso. Acrescenta `RotaPublica` (FR-010). |
| — | Workflow | Branch `005-telas-login-cadastro`; commit e push por checkpoint feitos pelo assistente, sem coautoria; PR e merge com o responsável (v1.2.0). | ✅ |

**Resultado**: nenhuma violação. O gate passou antes e depois do design; nada em Complexity
Tracking.

**Riscos aceitos** (spec): credenciais legíveis pela interface (Q4); sessão sobrevive a fechar o
navegador (Q2); HTTP na rede local até o RNF-09.

## Project Structure

### Documentation (this feature)

```text
specs/005-telas-login-cadastro/
├── plan.md
├── research.md          # R-01 a R-10
├── data-model.md        # sessão no navegador, estados, formulários
├── quickstart.md        # S1 a S10
├── contracts/
│   └── interface.md     # rotas, textos, uso da API, acessibilidade
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
testar.sh                    # novo: roda as suítes do backend e da interface (Princípio IV)

frontend/
├── package.json             # + react-router; devDeps de teste; script "test"
├── package-lock.json
├── vite.config.js           # + bloco test (jsdom, setupFiles)
└── src/
    ├── main.jsx             # + BrowserRouter, AuthProvider, estilos.css
    ├── App.jsx              # rotas
    ├── estilos.css          # novo: visual simples e responsivo (R-10)
    ├── testes/
    │   ├── preparacao.js    # novo: jest-dom, limpeza do localStorage e do fetch
    │   ├── renderizar.jsx   # novo: MemoryRouter + AuthProvider para os testes
    │   └── ambiente.test.js # novo: confere o ambiente de teste (localStorage, AbortSignal, fetch)
    ├── api/
    │   ├── client.js        # + requisitarAutenticada (Bearer, renovação única)
    │   ├── client.test.js
    │   ├── erros.js         # novo: interpretarErro
    │   ├── erros.test.js
    │   ├── sessao.js        # novo: entrar, renovar, sair, obterEu
    │   ├── usuarios.js      # novo: cadastrar
    │   └── saude.js         # sem mudança
    ├── auth/
    │   ├── armazenamento.js       # novo: lerSessao, salvarSessao, apagarSessao
    │   ├── armazenamento.test.js
    │   ├── AuthProvider.jsx       # novo: contexto + useAuth
    │   ├── AuthProvider.test.jsx
    │   ├── RotaProtegida.jsx      # novo
    │   ├── RotaPublica.jsx        # novo
    │   └── rotas.test.jsx         # guardas de rota
    ├── hooks/
    │   └── useSaudeApi.js   # sem mudança
    ├── components/
    │   ├── CampoTexto.jsx   # rótulo + campo + erros (aria)
    │   ├── AvisoFormulario.jsx  # mensagem geral (role="alert")
    │   ├── Layout.jsx       # cabeçalho + menu + <Outlet/>
    │   ├── Layout.test.jsx
    │   └── Rodape.jsx       # estado da API (antigo conteúdo do Inicio)
    └── pages/
        ├── Entrar/Entrar.jsx        + Entrar.test.jsx
        ├── Cadastro/Cadastro.jsx    + Cadastro.test.jsx
        ├── Inicio/Inicio.jsx        # saudação
        └── NaoEncontrada/NaoEncontrada.jsx  + NaoEncontrada.test.jsx
```

**Structure Decision**: segue a estrutura indicativa do `docs/arquitetura.md` §3. Os testes ficam
ao lado do código porque só `frontend/src/` é montado no container (spec 001).

## Complexity Tracking

Nenhuma violação.

## Pontos de atenção para a implementação

1. **Rebuild obrigatório** depois de mudar `package.json` ou `vite.config.js`
   (`docker compose up -d --build frontend`); instalar com os arquivos montados ([R-08](research.md)).
2. **`StrictMode` executa efeitos duas vezes** em desenvolvimento: a verificação inicial chama
   `/usuarios/eu/` duas vezes, e a renovação única (R-03) é o que impede a sessão de cair. Testar
   esse caso no `client.test.js`.
3. **`AbortSignal.timeout` no jsdom**: o cliente atual usa `AbortSignal.timeout(10000)`; confirmar
   que existe no ambiente de teste ou isolar a criação do sinal para poder simular.
4. **Rodapé de saúde** em todas as telas: confirmar que o quickstart da spec 001 continua válido
   (S10) e que o `useSaudeApi` não roda duas vezes por página.
5. **Fallback de SPA**: o Vite em modo dev serve `index.html` para `/entrar` e `/cadastro`
   abertos direto; o modo de uso (RNF-09) vai precisar do mesmo no servidor de produção.
