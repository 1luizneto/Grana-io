# Implementation Plan: Mês de Referência

**Branch**: `007-mes-referencia` | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-mes-referencia/spec.md`

**Backlog**: US-06 (Sprint 2). A tela (seletor de mês) é da US-27; o bloqueio de excluir mês com
gastos é da US-07 (Clarifications).

## Summary

Model `MesReferencia(OwnedModel)` no app `gastos` (mês 1–12, ano 2000–2100, `fechado`), único por
dono, em ordem cronológica, e a API `/api/meses/`: listar, criar, abrir, fechar/reabrir por
`PATCH {"fechado": ...}` e excluir só mês aberto. Mês e ano não mudam depois de criados. Tudo com o
kit de isolamento da spec 004. Detalhes em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (Django 5.2, DRF 3.18). Sem mudança na interface.

**Primary Dependencies**: nenhuma nova.

**Storage**: PostgreSQL; tabela nova `gastos_mesreferencia` (migration `gastos.0003`).

**Testing**: pytest + pytest-django; kit `CasosDeIsolamento`. `sh testar.sh`.

**Target Platform**: igual às specs anteriores.

**Project Type**: aplicação web; esta spec mexe só no backend.

**Performance Goals**: listagem indexada por dono, poucas linhas por pessoa.

**Constraints**: isolamento por dono; mês único por conta; faixas validadas na API e no banco; mês e
ano imutáveis; mês fechado não se exclui.

**Scale/Scope**: 1 model, 1 serializer, 1 viewset, 1 migration.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Princípio / regra | Avaliação pré-pesquisa | Pós-design |
|---|---|---|---|
| I | Localidade e privacidade | Dados locais. | ✅ |
| II | Isolamento por usuário | Registro com dono: `OwnedModel`, mixin, serializer base e kit. | ✅ `MesReferencia(OwnedModel)`, `MesReferenciaViewSet(FiltroPorDonoMixin, ...)`, subclasse do kit; guardas da spec 004 cobrem o model e a rota. |
| III | Precisão monetária | N/A (mês não tem valor). | ✅ N/A |
| IV | Testes obrigatórios (test-first) | Model e API com testes primeiro. | ✅ Quickstart S1 a S6. |
| V | Separação backend/frontend | Regras e rótulo MM/AAAA na API. | ✅ `rotulo` vem pronto ([R-06](research.md)); erros em `detail`/campo, no formato que a interface já trata ([R-05](research.md)). |
| VI | Simplicidade / incremental | Sem tela (US-27), sem copiar mês (US-09), sem recorrentes (US-07b). | ✅ `PATCH` em vez de ações extras ([R-02](research.md)); helper de unicidade local ao app ([R-07](research.md)). |
| — | `docs/arquitetura.md` | App de domínio `gastos`; views finas; sem signals. | ✅ |
| — | Workflow | Branch `007-mes-referencia`; commits por checkpoint pelo assistente, sem coautoria; PR e merge com o responsável. | ✅ |

**Resultado**: nenhuma violação; nada em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/007-mes-referencia/
├── plan.md
├── research.md          # R-01 a R-07
├── data-model.md
├── quickstart.md        # S1 a S6
├── contracts/
│   └── api-meses.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── gastos/
│   ├── models.py                       # + MesReferencia
│   ├── migrations/0003_mesreferencia.py
│   ├── serializers.py                  # + MesReferenciaSerializer
│   ├── views.py                        # + MesReferenciaViewSet; helper de unicidade (R-07)
│   └── urls.py                         # + router "meses"
└── tests/gastos/
    ├── test_meses_models.py
    └── test_meses_api.py               # inclui a subclasse do kit de isolamento
```

**Structure Decision**: mesmo app e mesmos padrões das categorias (spec 006).

## Complexity Tracking

Nenhuma violação.

## Pontos de atenção para a implementação

1. **`UniqueTogetherValidator` com `HiddenField`**: confirmar que o DRF gera o validador para
   `fields=["dono", "ano", "mes"]` e usa a mensagem da constraint ([R-03](research.md)).
2. **Kit de isolamento**: `criar(usuario)` gera meses diferentes a cada chamada (mesma lição da
   spec 006) e **já fechados**, com `payload_alteracao = {"fechado": False}`: o caso "o dono opera
   normalmente" faz `PATCH` e depois `DELETE`, e mês fechado não se exclui (achado I1 do analyze).
3. **`PATCH` com `mes`/`ano` iguais**: aceitar sem erro ([R-02](research.md)).
4. **Refatoração do `_salvar`**: as suítes de categorias continuam verdes depois de extrair o helper.
