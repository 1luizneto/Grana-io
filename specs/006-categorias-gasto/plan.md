# Implementation Plan: Categorias de Gasto

**Branch**: `006-categorias-gasto` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-categorias-gasto/spec.md`

**Backlog**: US-05 (Sprint 2), mais o critério da US-01 "categorias padrão no cadastro" (movido
para cá na spec 002). O critério da US-05 sobre excluir categoria com gastos fica com a US-07
(Clarifications Q2).

## Summary

Primeiro dado financeiro real, já sobre a regra de dono da spec 004:

- **Backend**: app novo `gastos` com `Categoria(OwnedModel)` (nome único por dono sem diferenciar
  maiúsculas, cor de uma paleta de 12); API `/api/categorias/` (CRUD) e `/api/categorias/cores/`
  (paleta); 7 categorias padrão criadas no cadastro, na mesma transação, e para contas antigas por
  migration de dados.
- **Interface**: tela `/categorias` no menu, com criação, edição na linha, seletor de cor por
  rádios e exclusão com confirmação.

Detalhes em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (Django 5.2, DRF 3.18) e JavaScript (React 19.3, Vite 8.3).

**Primary Dependencies**: nenhuma nova.

**Storage**: PostgreSQL. Tabela nova `gastos_categoria`; migration de dados para contas antigas
([R-05](research.md)).

**Testing**: pytest + pytest-django (kit `CasosDeIsolamento`, teste da migration com
`MigrationExecutor`); Vitest + Testing Library na interface. `sh testar.sh` roda tudo.

**Target Platform**: igual às specs anteriores.

**Project Type**: aplicação web (backend + interface).

**Performance Goals**: listar categorias é uma consulta indexada por dono, com poucas linhas; criar
uma categoria em até 30 s pela pessoa (SC-002).

**Constraints**:
- isolamento por dono (spec 004);
- nome único sem diferenciar maiúsculas, mas com acentos;
- paleta só no backend (Princípio V);
- cadastro e categorias padrão atômicos;
- 360 px e teclado na tela.

**Scale/Scope**: 1 model, 1 viewset (5 operações + paleta), 1 service, 2 migrations; 1 página,
1 hook, 1 componente de seletor de cor.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Princípio / regra | Avaliação pré-pesquisa | Pós-design |
|---|---|---|---|
| I | Localidade e privacidade | Dados locais; nada externo. | ✅ Paleta em código, sem recurso externo. |
| II | Isolamento por usuário | Primeiro registro com dono real: `OwnedModel`, mixin, serializer base e kit obrigatórios. | ✅ `Categoria(OwnedModel)`, `CategoriaViewSet(FiltroPorDonoMixin, ...)`, `CategoriaSerializer(RegistroComDonoSerializer)`, subclasse do kit; a guarda de models e de rotas cobre o app novo. |
| III | Precisão monetária | N/A (categoria não tem valor). | ✅ N/A |
| IV | Testes obrigatórios (test-first) | Model, service, API, migration de dados e tela com testes primeiro. | ✅ Inclui o teste da migration ([R-05](research.md)) e o kit. Quickstart S1 a S7. |
| V | Separação backend/frontend | Paleta e regras de nome só na API; a tela exibe e envia. | ✅ `/api/categorias/cores/` é a fonte da paleta; a ordem vem da API ([R-02](research.md), [R-09](research.md)). |
| VI | Simplicidade / incremental | Exclusão com destino adiada para a US-07; sem dependência nova. | ✅ Sem modal e sem biblioteca de cores; confirmação nativa. |
| — | `docs/arquitetura.md` | App de domínio `gastos` (§2.3); Service Layer para as categorias padrão; chamada explícita no cadastro, sem signals (§5); hook por recurso na interface (§3). | ✅ |
| — | Workflow | Branch `006-categorias-gasto`; commits por checkpoint feitos pelo assistente, sem coautoria; PR e merge com o responsável (v1.2.0). | ✅ |

**Resultado**: nenhuma violação; nada em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/006-categorias-gasto/
├── plan.md
├── research.md          # R-01 a R-09
├── data-model.md        # Categoria, paleta, categorias padrão
├── quickstart.md        # S1 a S7
├── contracts/
│   ├── api-categorias.md
│   └── tela-categorias.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── config/settings.py              # + "gastos" em INSTALLED_APPS
├── config/urls.py                  # + path("api/", include("gastos.urls"))
├── accounts/services/cadastro.py   # chama criar_categorias_padrao na mesma transação (R-04)
├── gastos/                         # novo app (R-01)
│   ├── apps.py
│   ├── cores.py                    # PALETA (12 cores), CODIGOS (R-02)
│   ├── models.py                   # Categoria(OwnedModel)
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   └── 0002_categorias_padrao_contas_existentes.py  # RunPython (R-05)
│   ├── services/
│   │   └── categorias.py           # CATEGORIAS_PADRAO, criar_categorias_padrao, escolher_cor_livre
│   ├── serializers.py              # CategoriaSerializer(RegistroComDonoSerializer)
│   ├── views.py                    # CategoriaViewSet + ação cores
│   └── urls.py                     # router /categorias/
└── tests/gastos/
    ├── test_categorias_service.py
    ├── test_categorias_api.py      # inclui a subclasse do kit de isolamento
    ├── test_cadastro_categorias.py # cadastro cria as padrão, atômico
    └── test_migration_categorias.py

frontend/src/
├── api/categorias.js               # listar, criar, atualizar, excluir, listarCores
├── hooks/useCategorias.js
├── components/SeletorCor.jsx       + SeletorCor.test.jsx
├── components/Layout.jsx           # + item "Categorias" no menu
├── pages/Categorias/Categorias.jsx + Categorias.test.jsx
├── App.jsx                         # + rota /categorias
└── estilos.css                     # + lista, amostras de cor e seletor
```

**Structure Decision**: app de domínio `gastos` no backend (§2.3); na interface, página + hook por
recurso + componente de apresentação (§3), reaproveitando `CampoTexto`, `AvisoFormulario`,
`interpretarErro` e `requisitarAutenticada` da spec 005.

## Complexity Tracking

Nenhuma violação.

## Pontos de atenção para a implementação

1. **Constraint com expressão** (`Lower("nome")`): o DRF não gera validador; a validação do nome
   fica no serializer e o `IntegrityError` de corrida vira 400 ([R-06](research.md)).
2. **Mensagem do limite de 50 caracteres**: confirmar o texto do DRF em pt-BR e ajustar o contrato.
3. **Migration de dados**: os nomes e cores ficam copiados dentro da migration; testar com
   `MigrationExecutor` em `transaction=True` (mais lento; um teste só).
4. **Cadastro**: o `except IntegrityError` do `cadastrar_usuario` precisa continuar valendo só para o
   e-mail ([R-04](research.md)); os testes da spec 002 seguem verdes.
5. **Guardas da spec 004**: o app `gastos` entra automaticamente na guarda de models e na de rotas.
