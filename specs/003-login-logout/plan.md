# Implementation Plan: Login e Logout

**Branch**: `003-login-logout` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-login-logout/spec.md`

**Backlog**: US-02, com as partes de tela cobertas pela US-26, + o critério do RNF-02 "A API exige
autenticação em todas as rotas, exceto login e cadastro" (com a verificação de saúde como exceção
registrada).

## Summary

Adiciona a sessão por JWT (`djangorestframework-simplejwt` 5.5.1, previsto na constituição), com
views e mensagens próprias em pt-BR:

- `POST /api/auth/entrar/`: e-mail e senha → credenciais de acesso (30 min) e de renovação
  (7 dias), mais nome e e-mail. Mensagem genérica "E-mail ou senha incorretos." para qualquer
  credencial recusada. Limite de 10 tentativas por minuto por dispositivo.
- `POST /api/auth/renovar/`: renovação de uso único (girada e bloqueada).
- `POST /api/auth/sair/`: bloqueia a credencial de renovação do próprio usuário.
- `GET /api/usuarios/eu/`: primeira rota protegida.

`JWTAuthentication` passa a ser a autenticação padrão, e toda rota nova nasce protegida. Para o
limite de tentativas enxergar o dispositivo real, o proxy do Vite passa a enviar
`X-Forwarded-For`. O backend só confia nesse cabeçalho quando a requisição vem do container do
frontend. Detalhes em [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.12 (backend); JavaScript (só `vite.config.js`).

**Primary Dependencies**: Django 5.2, DRF 3.18, **djangorestframework-simplejwt 5.5.1** (nova,
traz PyJWT 2.15.1).

**Storage**: PostgreSQL. Tabelas novas do `token_blacklist`, criadas pela migration da biblioteca e
aplicadas sozinhas na subida (spec 001).

**Testing**: pytest + pytest-django. Vencimento simulado com `set_exp`, sem dependência de relógio
([R-11](research.md)).

**Target Platform**: igual às specs anteriores.

**Project Type**: aplicação web. Esta spec mexe no backend e numa linha do `vite.config.js`.

**Performance Goals**: login em até 30 s pela pessoa (SC-001), dominado pelo hash PBKDF2 (~centenas
de ms).

**Constraints**:
- mensagem genérica idêntica nos três casos de credencial recusada;
- nenhum segredo em logs;
- limite de tentativas por dispositivo real, mesmo atrás do proxy;
- prazos configuráveis.

**Scale/Scope**: poucos usuários. 4 rotas, 1 throttle, 1 service de sessão.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Princípio / regra | Avaliação pré-pesquisa | Pós-design |
|---|---|---|---|
| I | Localidade e privacidade | Credenciais assinadas com a `SECRET_KEY` (já bloqueada fora do dev). Nada de senha ou credencial em logs. Nenhum serviço externo. | ✅ Credenciais de renovação ficam só no banco local. `sensitive_post_parameters` em entrar, renovar e sair. S9 verifica os logs. |
| II | Isolamento por usuário | Base para o isolamento: `request.user` passa a existir. `/usuarios/eu/` e sair só atuam sobre o próprio usuário. | ✅ `/usuarios/eu/` lê `request.user`. `sair` confere o `user_id` da credencial ([R-05](research.md)). Os testes cobrem outra pessoa. O `OwnedModel` fica na US-03. |
| III | Precisão monetária | N/A | ✅ N/A |
| IV | Testes obrigatórios (test-first) | Autenticação é core pela constituição. Testes antes para services, views, throttle e helper `env_int`. | ✅ Vencimento via `set_exp`, sem dependência nova. Quickstart S1 a S10. |
| V | Separação backend/frontend | Contrato documentado, com regra explícita para a interface (401 → renovar → login). | ✅ [contracts/api-sessao.md](contracts/api-sessao.md). A interface é a US-26. |
| VI | Simplicidade / incremental | US-02 (API). Uma dependência nova, prevista na constituição. | ✅ Sem freezegun, sem Redis para o throttle, sem bloqueio de conta. |
| — | Stack | "JWT (djangorestframework-simplejwt) com login por e-mail". | ✅ Exatamente isso. |
| — | `docs/arquitetura.md` | Views finas, service de sessão (`accounts/services/sessao.py`), sem signals. Nomenclatura pt-BR e `/api/usuarios/eu/` no plural. | ✅ |
| — | Workflow | Branch `003-login-logout`. Commits manuais. | ✅ |

**Resultado**: nenhuma violação, e o gate passou antes e depois do design. Não há nada em
Complexity Tracking.

**Riscos aceitos** (registrados na spec):
- a credencial de acesso vale até 30 min após a saída;
- HTTP na rede local até o RNF-09;
- dispositivos atrás do mesmo IP dividem o limite de tentativas.

## Project Structure

### Documentation (this feature)

```text
specs/003-login-logout/
├── plan.md
├── research.md          # R-01 a R-12
├── data-model.md        # sessão, token_blacklist, uso do Usuario
├── quickstart.md        # S1 a S10
├── contracts/
│   └── api-sessao.md    # entrar, renovar, sair, usuarios/eu, erros 401, variáveis
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
compose.yaml                     # + 4 variáveis GRANA_* no backend
.env.example                     # + 4 variáveis comentadas
frontend/vite.config.js          # proxy /api com xfwd: true (X-Forwarded-For)

backend/
├── requirements.txt             # + djangorestframework-simplejwt==5.5.1
├── config/
│   ├── env.py                   # + env_int(nome, padrao)
│   └── settings.py              # + apps simplejwt/token_blacklist; SIMPLE_JWT;
│                                #   DEFAULT_AUTHENTICATION_CLASSES; DEFAULT_THROTTLE_RATES;
│                                #   PROXY_CONFIAVEL
├── accounts/
│   ├── serializers.py           # + EntrarSerializer, RenovacaoSerializer, UsuarioSerializer
│   ├── services/
│   │   └── sessao.py            # autenticar, emitir_sessao, renovar_sessao, encerrar_sessao,
│   │                            #   SessaoInvalida
│   ├── throttles.py             # TentativasLoginThrottle (get_ident com proxy confiável)
│   ├── views.py                 # + EntrarView, RenovarView, SairView, EuView
│   └── urls.py                  # + auth/entrar/, auth/renovar/, auth/sair/, usuarios/eu/
└── tests/
    ├── conftest.py              # + fixture que limpa o cache (throttle)
    ├── config/test_env.py       # + env_int
    └── accounts/
        ├── test_sessao_service.py
        ├── test_throttles.py
        ├── test_entrar_api.py
        ├── test_renovar_sair_api.py
        └── test_protecao_api.py # /usuarios/eu/, rotas públicas vs. protegidas, 401 por tipo
```

**Structure Decision**: tudo no app `accounts` (`docs/arquitetura.md` §2.3), que já é dono do usuário
e da autenticação. O service de sessão é o único ponto que toca o simplejwt diretamente.

## Complexity Tracking

Nenhuma violação.

## Pontos de atenção para a implementação

1. **Instalar a dependência exige rebuild da imagem** (`docker compose up -d --build`), porque o
   `requirements.txt` muda.
2. **A troca de `DEFAULT_AUTHENTICATION_CLASSES` afeta todas as rotas.** Confirmar que saúde e
   cadastro continuam públicas: já declaram `authentication_classes = []`, e os testes da spec 001
   e 002 precisam continuar verdes.
3. **Verificar o `xfwd` no Vite 8** ([R-08](research.md)): se não for suportado, usar `configure`
   para definir o cabeçalho.
4. **O throttle usa o cache em memória**: o `conftest` precisa limpar o cache entre os testes, senão
   um teste afeta o outro.
