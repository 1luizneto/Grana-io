# Implementation Plan: Cadastro de Usuário

**Branch**: `002-cadastro-usuario` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-cadastro-usuario/spec.md`

**Backlog**: US-01, exceto o critério das categorias padrão, movido para a US-05 (Clarifications),
+ o critério do RNF-02 "Senhas são armazenadas com hash".

## Summary

Cria o app `accounts` com um modelo de usuário próprio, `Usuario`, identificado pelo e-mail
(`AUTH_USER_MODEL`). A definição acontece agora, antes que qualquer dado de domínio dependa do
usuário.

A rota pública `POST /api/usuarios/` faz o cadastro:
- valida os campos, com mensagens em pt-BR por campo;
- normaliza o e-mail e garante unicidade até sob concorrência (restrição no banco + tratamento do
  `IntegrityError`);
- aplica as regras de senha (validadores nativos do Django + lista pt-BR complementar);
- grava a senha com hash PBKDF2;
- responde só `nome` e `email`, sem autenticar.

O cadastro pode ser fechado por `GRANA_CADASTRO_ABERTO=0` (403). A orquestração fica num
application service transacional, onde a US-05 acrescentará as categorias padrão. Detalhes em
[research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (backend). Sem mudanças no frontend nesta spec.

**Primary Dependencies**: Django 5.2 LTS, Django REST Framework (já instalados). Nenhuma dependência
nova ([R-11](research.md)).

**Storage**: PostgreSQL 17 (spec 001). Tabela nova `accounts_usuario`, com o banco de
desenvolvimento recriado uma vez ([R-02](research.md)).

**Testing**: pytest + pytest-django, com `docker compose run --rm backend pytest`.

**Target Platform**: igual à spec 001 (Docker Compose, Windows/Linux).

**Project Type**: aplicação web. Esta spec altera só o backend.

**Performance Goals**: cadastro concluído pela pessoa em até 1 min (SC-001). A resposta da API é
dominada pelo hash PBKDF2, na casa de centenas de milissegundos, o que é aceitável.

**Constraints**:
- senha nunca em texto legível, em respostas, erros ou logs (FR-007);
- unicidade do e-mail sob concorrência (FR-004);
- mensagens em pt-BR (constituição, Stack);
- sem envio de e-mails.

**Scale/Scope**: poucos usuários (uma casa). 1 endpoint, 1 model, 1 validador, 1 service.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Princípio / regra | Avaliação pré-pesquisa | Pós-design |
|---|---|---|---|
| I | Localidade e privacidade | Dados locais. Senha nunca em respostas, erros ou logs. Nenhum serviço externo (sem e-mail). | ✅ `write_only` + serializer de saída + `sensitive_post_parameters` ([R-06](research.md)). Hash PBKDF2 ([R-05](research.md)). |
| II | Isolamento por usuário | O `Usuario` é o dono futuro, não um registro com dono. Nenhum dado de domínio nesta spec. Cadastro não lista nem expõe outros usuários. | ✅ Só `POST` (405 nos demais métodos). Resposta sem `id`. O `OwnedModel` fica para a US-03. |
| III | Precisão monetária | N/A | ✅ N/A |
| IV | Testes obrigatórios (test-first) | Model/manager, validador, service e endpoint são core e têm testes escritos antes. | ✅ Testes de model, validador, service (incluindo corrida) e API. Quickstart Q1 a Q9. |
| V | Separação backend/frontend | Contrato REST documentado. O frontend não muda (tela na US-26). | ✅ [contracts/api-cadastro.md](contracts/api-cadastro.md) |
| VI | Simplicidade / incremental | US-01 do backlog. Categorias adiadas para a US-05 (clarificação). Sem dependências novas. | ✅ Sem Argon2, sem CITEXT, sem signals, sem flag no banco ([R-03](research.md), [R-04](research.md), [R-05](research.md), [R-07](research.md)). |
| — | Stack | Django 5.2 + DRF, pytest. JWT com login por e-mail na US-02: o `USERNAME_FIELD = "email"` prepara isso. | ✅ |
| — | `docs/arquitetura.md` | App `accounts` (§2.3). View fina → serializer → application service com `transaction.atomic` (§2.2). Sem signals (§5). Nomenclatura pt-BR e rota no plural (§4). | ✅ `CadastroView` → `CadastroSerializer` → `cadastrar_usuario()`. Rota `/api/usuarios/`. |
| — | Workflow | Branch `002-cadastro-usuario` = diretório da spec. Commits manuais. | ✅ |

**Resultado**: nenhuma violação, e o gate passou antes e depois do design. Não há nada em
Complexity Tracking.

**Riscos aceitos**:
- a mensagem de e-mail duplicado revela a existência de uma conta (critério explícito do backlog,
  rede local);
- sem limite de tentativas de cadastro (spec, Assumptions).

## Project Structure

### Documentation (this feature)

```text
specs/002-cadastro-usuario/
├── plan.md              # Este arquivo
├── research.md          # Phase 0: R-01 a R-11
├── data-model.md        # Phase 1: Usuario + configuração
├── quickstart.md        # Phase 1: roteiro Q1 a Q9
├── contracts/
│   └── api-cadastro.md  # POST /api/usuarios/ + GRANA_CADASTRO_ABERTO
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
compose.yaml                 # + GRANA_CADASTRO_ABERTO no backend
.env.example                 # + GRANA_CADASTRO_ABERTO

backend/
├── config/
│   ├── settings.py          # + "accounts" em INSTALLED_APPS; AUTH_USER_MODEL;
│   │                        #   AUTH_PASSWORD_VALIDATORS (+ SenhaComumPtBrValidator); CADASTRO_ABERTO
│   └── urls.py              # + path("api/", include("accounts.urls"))
├── accounts/
│   ├── __init__.py
│   ├── apps.py              # AccountsConfig
│   ├── models.py            # Usuario, UsuarioManager
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py  # gerada com makemigrations, no container
│   ├── validators.py        # SenhaComumPtBrValidator
│   ├── serializers.py       # CadastroSerializer (entrada), UsuarioCadastradoSerializer (saída)
│   ├── services/
│   │   ├── __init__.py
│   │   └── cadastro.py      # cadastro_aberto(), cadastrar_usuario(), EmailJaCadastrado
│   ├── views.py             # CadastroView (POST, AllowAny, sensitive_post_parameters)
│   └── urls.py              # usuarios/
└── tests/
    └── accounts/
        ├── __init__.py
        ├── test_models.py              # manager: normalização, hash, sem privilégios; superuser
        ├── test_validators.py          # SenhaComumPtBrValidator
        ├── test_cadastro_service.py    # atomicidade, corrida (IntegrityError → duplicado), fechado
        └── test_cadastro_api.py        # 201/400/403/405, mensagens, sem senha/token, sem dados em erro
```

**Structure Decision**: segue `docs/arquitetura.md` §2.3. O app `accounts` é dono do usuário e da
autenticação e receberá o login (US-02) e o perfil (US-04). Os testes espelham o app em
`backend/tests/accounts/`. O frontend não muda: a tela de cadastro é a US-26.

## Complexity Tracking

Nenhuma violação da constituição ou de `docs/arquitetura.md`.

## Pontos de atenção para a implementação

1. **Recriar o banco uma vez** (`docker compose down -v`) depois da primeira migration de
   `accounts` ([R-02](research.md)). Só há dados de teste, mas é uma ação destrutiva e deve ficar
   explícita no checkpoint.
2. **`AUTH_USER_MODEL` precisa ser definido antes de gerar a migration**, senão o Django cria o
   histórico apontando para `auth.User`.
3. A guarda `tests/test_migrations.py` (spec 001) vai falhar enquanto `0001_initial` não for
   gerada. Isso é esperado no ciclo test-first.
