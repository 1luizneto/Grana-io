# Implementation Plan: Gastos Fixos

**Branch**: `010-gastos-fixos` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Backlog**: US-07b (Sprint 2).

## Summary

Model `GastoFixo` e a origem `Gasto.fixo`; API `/api/fixos/`; geração dos gastos fixos na criação
do mês (mesma transação); "Repetir todo mês" no lançamento; categoria excluída leva os fixos; tela
"Gastos fixos" e as marcas na tela do mês. Detalhes em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (Django 5.2, DRF 3.18); JavaScript (React 19, Vite 8).

**Primary Dependencies**: nenhuma nova.

**Storage**: PostgreSQL; tabela `gastos_gastofixo` e coluna `gastos_gasto.fixo_id` (migration
`gastos.0005`).

**Testing**: pytest (kit de isolamento) e Vitest + Testing Library; validação no navegador.

**Project Type**: aplicação web (backend e frontend).

**Constraints**: `Decimal`; isolamento; meses existentes nunca mudam por causa de fixos; criação do
mês atômica.

**Scale/Scope**: 1 model + 1 campo, 1 service, 1 viewset, 3 rotas alteradas, 1 tela nova, 2 telas
alteradas.

## Constitution Check

| # | Princípio / regra | Avaliação | Pós-design |
|---|---|---|---|
| I | Localidade | Dados locais. | ✅ |
| II | Isolamento | Fixo com dono; categoria só da pessoa. | ✅ `GastoFixo(OwnedModel)`, mixin, `RelacionadoDoDonoField`, kit; geração usa `do_dono` do mês. |
| III | Precisão monetária | Valor `Decimal`; geração copia o valor sem cálculo. | ✅ |
| IV | Test-first | Model, service, API e telas com testes primeiro. | ✅ |
| V | Separação | Geração e regras no backend. | ✅ A tela só envia `repetir` e exibe. |
| VI | Simplicidade | Geração como função, sem agendador. | ✅ |
| — | `docs/arquitetura.md` | Caso de uso "criar mês" previsto para a US-07b. | ✅ `services/fixos.py` chamado no `perform_create` do mês. |
| — | Workflow | Branch empilhada sobre a 009 (modo autônomo). | ✅ |

**Resultado**: nenhuma violação.

## Project Structure

```text
backend/gastos/models.py              # + GastoFixo; Gasto.fixo
backend/gastos/migrations/0005_*.py
backend/gastos/serializers.py         # + MesAnoField, GastoFixoSerializer; GastoSerializer (fixo, repetir)
backend/gastos/services/fixos.py      # gerar_gastos_fixos, criar_fixo_do_gasto
backend/gastos/services/gastos.py     # excluir_categoria considera fixos
backend/gastos/views.py               # + GastoFixoViewSet; mês gera fixos; gasto com repetir
backend/gastos/urls.py                # + "fixos"
backend/tests/gastos/test_fixos_models.py, test_fixos_service.py, test_fixos_api.py
frontend/src/api/fixos.js, hooks/useFixos.js
frontend/src/pages/Fixos/Fixos.jsx (+ .test.jsx)
frontend/src/components/FormularioGasto.jsx, TabelaGastos.jsx, Layout.jsx (+ testes)
frontend/src/App.jsx, estilos.css
```

## Complexity Tracking

Nenhuma violação.

## Pontos de atenção

1. **Teste de chaves do gasto** (spec 008, `test_lancar`): passa a incluir `"fixo"`.
2. **Kit de isolamento**: `montar_payload_criacao` com a categoria da Ana; `criar` sem unicidade.
3. **Atomicidade**: falha na geração (simulada) não pode deixar o mês criado.
4. **`type="month"` no jsdom**: o valor é texto `AAAA-MM`; testar com `fireEvent.change`/`clear` +
   `type` conforme o suporte do Testing Library.
