# Implementation Plan: Tela do Mês

**Branch**: `009-tela-mes` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-tela-mes/spec.md`

**Backlog**: US-27 (Sprint 2), com as pendências de tela da US-05, US-06, US-08 e do RNF-03.

## Summary

Tela "Gastos do mês" em `/meses/:id`: seletor e criação de mês, fechar/reabrir/excluir mês, totais
da API, formulário rápido para lançar e editar gastos, tabela com filtro e ordenação, confirmação
ao excluir e retorno de cada operação. Na tela de categorias, a exclusão passa a perguntar para
onde vão os gastos. Só frontend; usa a API das specs 006 a 008. Detalhes em
[research.md](research.md).

## Technical Context

**Language/Version**: JavaScript (React 19, Vite 8, react-router 8.4). Backend sem mudança.

**Primary Dependencies**: nenhuma nova.

**Storage**: nenhum novo (sessão no `localStorage`, spec 005).

**Testing**: Vitest + Testing Library (padrão da spec 005: `renderizarComRotas`, `simularApi`);
validação no navegador.

**Target Platform**: navegadores atuais, de 360 px de largura em diante.

**Project Type**: aplicação web; esta spec mexe só no frontend.

**Performance Goals**: lançar um gasto em menos de 30 s (SC-001); recarregar gastos e totais em
paralelo.

**Constraints**: sem cálculos financeiros na tela (Princípio V, RNF-03); acessível por teclado e
leitor de tela; sem rolagem horizontal.

**Scale/Scope**: 1 página nova (com 5 componentes), 2 hooks, 2 módulos de API, 1 módulo de
formatação; mudança na tela de categorias e no menu.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Princípio / regra | Avaliação pré-pesquisa | Pós-design |
|---|---|---|---|
| I | Localidade e privacidade | Nada sai da máquina; sem recursos externos. | ✅ |
| II | Isolamento por usuário | Garantido pela API; a tela só usa a sessão. | ✅ Mês de outra conta no endereço → "Mês não encontrado." (a lista é da própria pessoa). |
| III | Precisão monetária | A tela não calcula. | ✅ Totais da API; formatação e ordenação por texto/`BigInt` ([R-03](research.md)). |
| IV | Testes obrigatórios | Lógica de tela e formatação com testes primeiro. | ✅ `formatacao.test.js`, `Mes.test.jsx`, testes da tela de categorias e do menu. |
| V | Separação backend/frontend | Regras e mensagens vêm da API. | ✅ Erros exibidos como chegam; nenhuma validação de negócio na tela além de formato. |
| VI | Simplicidade | Sem bibliotecas de formulário, tabela ou estado. | ✅ |
| — | `docs/arquitetura.md` §3 | Hooks por recurso; página busca dados, componentes exibem. | ✅ `useMeses`, `useGastosDoMes`; componentes de apresentação em `components/`. |
| — | Workflow | Branch `009-tela-mes` empilhada sobre a 008 (modo autônomo). | ✅ |

**Resultado**: nenhuma violação.

## Project Structure

```text
specs/009-tela-mes/
├── plan.md, research.md (R-01 a R-10), quickstart.md (S1 a S9), tasks.md
├── contracts/tela-mes.md
└── checklists/requirements.md

frontend/src/
├── api/meses.js, api/gastos.js            # novos
├── api/categorias.js                       # excluirCategoria(id, moverPara)
├── hooks/useMeses.js, hooks/useGastosDoMes.js
├── utils/formatacao.js (+ .test.js)
├── components/AvisoFormulario.jsx          # tipo "sucesso" com role="status"
├── components/SeletorMes.jsx               # select de mês + formulário "Novo mês"
├── components/FormularioGasto.jsx
├── components/TabelaGastos.jsx             # filtro, ordenação e tabela
├── components/TotaisMes.jsx
├── components/Layout.jsx                   # menu "Gastos do mês"
├── pages/Mes/Mes.jsx (+ Mes.test.jsx)      # /meses e /meses/:id
├── pages/Categorias/Categorias.jsx         # painel de exclusão com destino
├── pages/Inicio/Inicio.jsx                 # link para "Gastos do mês"
├── App.jsx                                 # rotas
└── estilos.css
```

## Complexity Tracking

Nenhuma violação.

## Pontos de atenção para a implementação

1. **`simularApi` e query string**: as rotas simuladas casam pelo fim do endereço; usar chaves como
   `/gastos/?mes=7`.
2. **StrictMode**: efeitos rodam duas vezes nos testes; o redirecionamento de `/meses` precisa ser
   idempotente (`replace`).
3. **Data de hoje nos testes**: fixar com `vi.useFakeTimers({ toFake: ['Date'] })` /
   `vi.setSystemTime`, sem congelar os timers do Testing Library.
4. **Foco e anúncios**: depois de lançar, foco na descrição; mensagens de sucesso em
   `role="status"`.
5. **Tela de categorias**: os testes de exclusão da spec 006 (com `window.confirm`) mudam para o
   painel.
