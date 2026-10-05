# Data Model: Login e Logout

**Feature**: `003-login-logout` | **Data**: 2026-09-30 | **Plano**: [plan.md](plan.md)

Esta feature **não cria models próprios**. Ela usa o `Usuario` (spec 002) e as tabelas do app
`rest_framework_simplejwt.token_blacklist` ([research R-12](research.md)).

## Sessão (não persistida como entidade própria)

Uma sessão é o par de credenciais emitido no login:

| Credencial | Formato | Duração padrão | Conteúdo relevante | Guardada no banco? |
|---|---|---|---|---|
| Acesso (`acesso`) | JWT assinado com a `SECRET_KEY` | 30 min (`GRANA_SESSAO_ACESSO_MINUTOS`) | `user_id`, `exp`, `jti`, `token_type="access"` | Não |
| Renovação (`renovacao`) | JWT assinado com a `SECRET_KEY` | 7 dias (`GRANA_SESSAO_RENOVACAO_DIAS`) | `user_id`, `exp`, `jti`, `token_type="refresh"` | Sim, em `OutstandingToken` |

**Ciclo de vida da credencial de renovação**

```text
emitida (entrar)           ── renovar ──►  bloqueada  +  nova emitida
emitida                    ── sair ─────►  bloqueada
emitida                    ── 7 dias ───►  vencida (recusada; removível com flushexpiredtokens)
emitida (conta desativada) ── renovar ──►  recusada
```

A credencial de acesso não tem estado no servidor: vale até vencer, e é recusada antes disso só se
a conta for desativada (FR-014). Ver edge case "Credencial de acesso após a saída" na spec.

## Tabelas do `token_blacklist` (simplejwt)

| Tabela | Campos principais | Uso |
|---|---|---|
| `token_blacklist_outstandingtoken` | `user` (FK → `accounts.Usuario`), `jti` (único), `token`, `created_at`, `expires_at` | Registro de cada credencial de renovação emitida |
| `token_blacklist_blacklistedtoken` | `token` (1:1 → OutstandingToken), `blacklisted_at` | Credenciais de renovação que não podem mais ser usadas (renovadas ou encerradas) |

As credenciais de renovação ficam no banco local, que é o mesmo lugar dos dados financeiros
(constituição, Princípio I). Nunca vão para logs (FR-013).

## Usuario (spec 002): uso novo

| Campo | Uso nesta feature |
|---|---|
| `last_login` | Atualizado a cada login bem-sucedido (FR-005) |
| `is_active` | `False` → login recusado com mensagem genérica; credenciais de acesso e renovação recusadas (FR-003, FR-014) |

## Regras de validação (entrada)

| Rota | Campo | Regra | Mensagem |
|---|---|---|---|
| entrar | `email` | obrigatório | "Este campo é obrigatório." |
| entrar | `senha` | obrigatório; sem corte de espaços | "Este campo é obrigatório." |
| entrar | — | credenciais recusadas | 401 "E-mail ou senha incorretos." |
| entrar | — | mais de N tentativas/min do dispositivo | 429 "Muitas tentativas. Tente novamente em instantes." |
| renovar | `renovacao` | obrigatório; válida, não vencida, não bloqueada, de conta ativa | 401 "Sessão expirada ou encerrada. Entre novamente." |
| sair | `renovacao` | obrigatório; válida e do próprio usuário | 400 "Sessão inválida ou já encerrada." |

## Configuração

Ver [research R-10](research.md): `GRANA_SESSAO_ACESSO_MINUTOS`, `GRANA_SESSAO_RENOVACAO_DIAS`,
`GRANA_LOGIN_TENTATIVAS_POR_MINUTO` e `GRANA_PROXY_CONFIAVEL`.
