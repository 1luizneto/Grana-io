# Implementation Plan: Lançar, Editar e Excluir Gastos

**Branch**: `008-lancar-gastos` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-lancar-gastos/spec.md`

**Backlog**: US-07 e US-08 (Sprint 2), com os critérios herdados das US-05 e US-06 e os dois
primeiros critérios do RNF-03. A tela (formulário, confirmação, destino ao excluir categoria) é da
US-27 (próxima spec).

## Summary

Model `Gasto(OwnedModel)` no app `gastos` (descrição, valor `Decimal`, data, forma de pagamento,
mês e categoria com `RESTRICT`), a API `/api/gastos/` (CRUD com filtros por mês e categoria e lista
de formas de pagamento), os totais em `/api/meses/{id}/totais/`, e as regras que cruzam modelos num
service: mês fechado bloqueia gastos, mês com gastos não se exclui, categoria com gastos só se
exclui com destino. Detalhes em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (Django 5.2, DRF 3.18). Sem mudança na interface.

**Primary Dependencies**: nenhuma nova.

**Storage**: PostgreSQL; tabela nova `gastos_gasto` (migration `gastos.0004`).

**Testing**: pytest + pytest-django; kit `CasosDeIsolamento` (com o gancho novo do R-09).

**Target Platform**: igual às specs anteriores.

**Project Type**: aplicação web; esta spec mexe só no backend.

**Performance Goals**: totais com uma consulta agregada; dezenas a centenas de gastos por mês.

**Constraints**: `Decimal` exato (Princípio III); isolamento por dono; mês fechado; sem perder
gastos ao excluir mês ou categoria.

**Scale/Scope**: 1 model, 1 módulo de dinheiro, 1 service, 1 serializer, 1 viewset, 2 rotas
alteradas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Princípio / regra | Avaliação pré-pesquisa | Pós-design |
|---|---|---|---|
| I | Localidade e privacidade | Dados locais. | ✅ |
| II | Isolamento por usuário | Gasto com dono; mês e categoria referenciados só da própria pessoa. | ✅ `Gasto(OwnedModel)`, `FiltroPorDonoMixin`, `RelacionadoDoDonoField` para `mes` e `categoria`, kit com gancho de payload (R-09); filtros da lista rodam depois do filtro por dono (R-05). |
| III | Precisão monetária | `DecimalField` e `Decimal`; regra de arredondamento única; cálculos em service. | ✅ `core/dinheiro.py` (ROUND_HALF_UP, 2 casas; R-02); totais no `services/gastos.py` com `Sum` em `Decimal` (R-06); mais de 2 casas é recusado, nunca arredondado em silêncio. |
| IV | Testes obrigatórios (test-first) | Model, service e API com testes primeiro. | ✅ Quickstart S1 a S7; teste de exclusão da conta em cascata. |
| V | Separação backend/frontend | Totais e regras na API. | ✅ Totais prontos em `/totais/`; valores como texto com 2 casas; erros no formato que a interface já trata. |
| VI | Simplicidade / incremental | Sem tela, recorrentes ou parcelas. | ✅ Filtros sem `django-filter`; sem paginação; totais como ação da viewset de meses. |
| — | `docs/arquitetura.md` | Regra com mais de um model → service. | ✅ `services/gastos.py` (R-03); views só traduzem `RegraViolada` em 400. |
| — | Workflow | Branch `008-lancar-gastos` (empilhada sobre a 007, modo autônomo); commits por checkpoint, sem coautoria; PR e merge com o responsável. | ✅ |

**Resultado**: nenhuma violação; nada em Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/008-lancar-gastos/
├── plan.md
├── research.md          # R-01 a R-09
├── data-model.md
├── quickstart.md        # S1 a S7
├── contracts/
│   └── api-gastos.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── core/
│   └── dinheiro.py                      # CENTAVO, arredondar (R-02)
├── gastos/
│   ├── models.py                        # + FORMAS_PAGAMENTO, Gasto
│   ├── migrations/0004_gasto.py
│   ├── serializers.py                   # + GastoSerializer
│   ├── services/gastos.py               # RegraViolada, exigir_mes_aberto, verificar_exclusao_do_mes,
│   │                                    #   excluir_categoria, totais_do_mes
│   ├── views.py                         # + GastoViewSet; totais; destroy de mês e categoria
│   └── urls.py                          # + router "gastos"
└── tests/
    ├── isolamento.py                    # + gancho montar_payload_criacao (R-09)
    ├── core/test_dinheiro.py
    └── gastos/
        ├── test_gastos_models.py
        ├── test_gastos_service.py
        └── test_gastos_api.py           # inclui a subclasse do kit
```

**Structure Decision**: mesmo app `gastos` e mesmos padrões das specs 006 e 007.

## Complexity Tracking

Nenhuma violação.

## Pontos de atenção para a implementação

1. **`RESTRICT` e exclusão da conta**: confirmar com teste que apagar o usuário apaga categorias,
   meses e gastos sem `RestrictedError` (R-01).
2. **Mensagens do `DecimalField`**: confirmar as chaves de erro do DRF 3.18 (`invalid`,
   `min_value`, `max_decimal_places`, `max_digits`, `max_whole_digits`) e que `"12,50"` cai em
   `invalid` (R-02).
3. **Data contra o mês em `PATCH` parcial**: usar o mês e a data atuais quando não vierem no
   pedido; a data só é conferida se mês e data forem válidos.
4. **Ordem das regras**: erros de campo antes do mês fechado (R-04); o kit faz `PATCH` e `DELETE`
   num mês aberto.
5. **Spec 007**: a regra de mês fechado no `perform_destroy` dos meses passa para o service, sem
   mudar a resposta; a suíte de meses continua verde.
