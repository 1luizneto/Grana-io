# Implementation Plan: Isolamento de Dados por Usuário

**Branch**: `004-isolamento-usuario` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-isolamento-usuario/spec.md`

**Backlog**: US-03, mais a parte "incluindo o isolamento entre usuários" do critério do RNF-05
sobre testes de integração.

## Summary

Cria a regra comum de dono que todos os registros de dados financeiros vão herdar a partir da
US-05, junto com as guardas que impedem um registro de nascer sem isolamento:

- `core.models.OwnedModel`: model abstrato com `dono` (FK, cascade, não editável) e o queryset
  `do_dono(usuario)`;
- `core.mixins.FiltroPorDonoMixin`: filtra o `get_queryset()` pelo usuário da sessão e define o
  dono na criação. Registro de outra conta vira o mesmo 404 de um inexistente;
- `core.serializers.RegistroComDonoSerializer` (`dono` como `HiddenField`, ignorado no payload) e
  `RelacionadoDoDonoField` (referências só para registros do mesmo dono);
- guardas na suíte: todo model do projeto herda de `OwnedModel` (exceto `Usuario`), e toda view
  sobre `OwnedModel` usa o mixin;
- kit `tests/isolamento.py` (`CasosDeIsolamento`), que dá às próximas USs os testes de isolamento
  só com configuração.

O isolamento é provado com um app de exemplo que existe só nos testes (`tests.exemplo`, decisão A
da clarificação). Detalhes em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (backend). Sem mudança no frontend.

**Primary Dependencies**: Django 5.2, DRF 3.18 (já instalados). Nenhuma dependência nova.

**Storage**: PostgreSQL. **Nenhuma tabela nova no banco de uso.** `OwnedModel` é abstrato, e os
models de exemplo existem só no banco de testes, com migration própria aplicada só lá ([R-07](research.md)).

**Testing**: pytest + pytest-django. Novo `config/settings_test.py`, que acrescenta o app de
exemplo, e o marcador `@pytest.mark.urls` para as rotas de exemplo.

**Target Platform**: igual às specs anteriores.

**Project Type**: aplicação web. Esta spec mexe só no backend (código de base e testes).

**Performance Goals**: o filtro por dono é uma condição sobre coluna indexada (FK). Sem meta
própria.

**Constraints**:
- 404 idêntico para registro de outra conta, inexistente e mal formado;
- dono nunca vindo do payload;
- nenhum rastro do exemplo no banco de uso ou nas rotas da aplicação.

**Scale/Scope**: 1 model abstrato, 1 mixin, 2 classes de serializer, 2 guardas, 1 kit de testes e
1 app de exemplo de testes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Princípio / regra | Avaliação pré-pesquisa | Pós-design |
|---|---|---|---|
| I | Localidade e privacidade | Nada sai da máquina. O isolamento reforça a privacidade entre contas da mesma casa. | ✅ A API nunca expõe `dono` (nem ids de outras contas). |
| II | Isolamento por usuário | É o próprio princípio: base comum de "registro com dono", filtro antes de tudo, dono pelo servidor, 404 e não 403, teste de isolamento por endpoint. | ✅ R-01 a R-04 cobrem cada frase do princípio. Guardas (R-06) e kit (R-08) tornam a regra estrutural. A exceção dos dados de referência compartilhados (v1.2.0) vira a lista `MODELS_SEM_DONO`, hoje só com o `Usuario`. |
| III | Precisão monetária | N/A nesta spec. | ✅ O `ItemExemplo.valor` usa `DecimalField`, como modelo para as próximas USs. |
| IV | Testes obrigatórios (test-first) | Isolamento é core pela constituição. Testes antes de `OwnedModel`, mixin e serializers. | ✅ Kit, guardas e exemplo escritos primeiro e confirmados falhando. Quickstart S1 a S6. |
| V | Separação backend/frontend | Sem tela. A interface só exibe o que a API devolve. | ✅ [contracts/isolamento.md](contracts/isolamento.md) é a referência para os contratos das próximas USs. |
| VI | Simplicidade / incremental | US-03 sem registro real (clarificação A). Sem dependência nova. | ✅ Só o padrão previsto no documento de arquitetura. O app de exemplo fica fora da aplicação. |
| — | `docs/arquitetura.md` | §2.2 "Abstract Base Model + Mixin": `core.models.OwnedModel` + mixin de queryset por dono com `perform_create`. §2.3: base no `core`. Sem signals e sem thread-local. | ✅ Exatamente isso. O `HiddenField` no serializer complementa o `perform_create` (R-03). |
| — | Workflow | Branch `004-isolamento-usuario`. Marcos por checkpoint com commit e push feitos pelo assistente, sem coautoria; PR e merge com o responsável (constituição v1.2.0). | ✅ |

**Resultado**: nenhuma violação. O gate passou antes e depois do design, e não há nada em
Complexity Tracking.

**Limite aceito** (R-06): a suíte não verifica sozinha se cada US escreveu os testes de
isolamento. Isso é coberto pelo kit, pelo tasks.md de cada US e pelo Constitution Check.

## Project Structure

### Documentation (this feature)

```text
specs/004-isolamento-usuario/
├── plan.md
├── research.md          # R-01 a R-10
├── data-model.md        # OwnedModel, convenções, models de exemplo
├── quickstart.md        # S1 a S6
├── contracts/
│   └── isolamento.md    # regras que todo endpoint de dados segue
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── pytest.ini                   # DJANGO_SETTINGS_MODULE = config.settings_test
├── config/
│   └── settings_test.py         # novo: importa settings e acrescenta "tests.exemplo"
├── core/
│   ├── models.py                # novo: OwnedModel (abstrato) + RegistroDoDonoQuerySet
│   ├── mixins.py                # novo: FiltroPorDonoMixin
│   └── serializers.py           # novo: RegistroComDonoSerializer, RelacionadoDoDonoField
└── tests/
    ├── conftest.py              # + usuario, outro_usuario, cliente, cliente_autenticado
    │                            #   (movidas de tests/accounts/conftest.py) e cliente_da_bia
    ├── rotas.py                 # novo: rotas() extraída de test_protecao_api.py
    ├── isolamento.py            # novo: kit CasosDeIsolamento (R-08) e modelos_sem_dono() (R-06)
    ├── accounts/
    │   ├── conftest.py          # fica só com o que é específico de accounts (ou some)
    │   └── test_protecao_api.py # passa a importar tests.rotas
    ├── core/
    │   ├── test_owned_model.py        # do_dono, cascade, dono não editável
    │   ├── test_serializers_dono.py   # HiddenField, RelacionadoDoDonoField, unicidade
    │   └── test_guarda_isolamento.py  # guardas de models e de rotas
    └── exemplo/                 # app só de testes (migration só no banco de testes)
        ├── __init__.py
        ├── apps.py
        ├── models.py            # GrupoExemplo, ItemExemplo
        ├── serializers.py
        ├── views.py             # viewsets com FiltroPorDonoMixin, busca e ação total
        ├── urls.py              # config.urls + /api/exemplo/...
        └── test_isolamento_exemplo.py  # subclasse do kit + casos específicos
```

**Structure Decision**: a base fica no `core` (`docs/arquitetura.md` §2.3: "OwnedModel, mixins").
O exemplo fica dentro de `tests/`, porque ele é infraestrutura de teste e não pode aparecer na
aplicação (FR-013).

## Complexity Tracking

Nenhuma violação.

## Pontos de atenção para a implementação

1. **Docker Desktop estava desligado no planejamento.** Ligar antes do `/speckit-implement`. Os
   pontos abaixo dependem do DRF instalado no container.
2. **Mensagem de unicidade** ([R-05](research.md)): verificar se o DRF 3.18 usa a
   `violation_error_message` da `UniqueConstraint`. Se não usar, trocar a mensagem no
   `RegistroComDonoSerializer` para não citar `dono`.
3. **App sem migrations** ([R-07](research.md)): confirmar que o banco de testes cria as tabelas
   do `tests.exemplo` e que o `makemigrations --check` (guarda da spec 001) continua passando. Se
   não passar, criar a migration inicial do app de exemplo. **Resolvido na T009**: precisou da
   migration inicial, por causa da FK para `accounts_usuario`.
4. **Texto do 404 em pt-BR** ([R-10](research.md)): confirmar `"Não encontrado."` e ajustar o
   contrato se for diferente.
5. **Troca do `DJANGO_SETTINGS_MODULE` no `pytest.ini`**: os 126 testes atuais precisam continuar
   verdes com o `settings_test`. A guarda de proteção de rotas segue usando o `ROOT_URLCONF` real.
6. **Mover fixtures** para `tests/conftest.py` sem mudar nomes, para não mexer nos testes das
   specs 002 e 003.
