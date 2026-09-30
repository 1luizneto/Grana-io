# Contrato: Sessão (entrar, renovar, sair) e própria conta

**Feature**: `003-login-logout` | **Requisitos**: FR-001 a FR-015

Todas as rotas usam `Content-Type: application/json`. As rotas protegidas exigem o cabeçalho
`Authorization: Bearer <acesso>`.

---

## `POST /api/auth/entrar/`

Pública. Limitada a `GRANA_LOGIN_TENTATIVAS_POR_MINUTO` tentativas por minuto por dispositivo
(padrão 10).

**Requisição**

```json
{ "email": " Ana@Exemplo.com ", "senha": "uma-senha-boa-2026" }
```

**200 OK**

```json
{
  "acesso": "<credencial de acesso>",
  "renovacao": "<credencial de renovação>",
  "usuario": { "nome": "Ana Souza", "email": "ana@exemplo.com" }
}
```

**400 Bad Request**: campo ausente.

```json
{ "email": ["Este campo é obrigatório."], "senha": ["Este campo é obrigatório."] }
```

**401 Unauthorized**: e-mail inexistente, senha errada ou conta desativada. A resposta é
**idêntica** nos três casos.

```json
{ "detail": "E-mail ou senha incorretos." }
```

**429 Too Many Requests**: limite de tentativas estourado. Traz o cabeçalho `Retry-After`, em
segundos.

```json
{ "detail": "Muitas tentativas. Tente novamente em instantes." }
```

---

## `POST /api/auth/renovar/`

Pública. Troca a credencial de renovação por um par novo, e a enviada deixa de valer.

**Requisição**: `{ "renovacao": "<credencial de renovação>" }`

**200 OK**

```json
{ "acesso": "<nova credencial de acesso>", "renovacao": "<nova credencial de renovação>" }
```

**400 Bad Request**: `{ "renovacao": ["Este campo é obrigatório."] }`

**401 Unauthorized**: vencida, adulterada, já usada, encerrada por saída ou de conta desativada.

```json
{ "detail": "Sessão expirada ou encerrada. Entre novamente." }
```

---

## `POST /api/auth/sair/`

**Protegida.** Encerra a sessão: bloqueia a credencial de renovação informada, que precisa ser do
próprio usuário. As outras sessões da conta continuam válidas.

**Requisição**: `{ "renovacao": "<credencial de renovação desta sessão>" }`

**204 No Content**: sessão encerrada.

**400 Bad Request**: renovação ausente, inválida, vencida, já encerrada ou de outra pessoa. Nada é
bloqueado.

```json
{ "renovacao": ["Sessão inválida ou já encerrada."] }
```

**401 Unauthorized**: sem credencial de acesso válida (ver "Erros de autenticação").

---

## `GET /api/usuarios/eu/`

**Protegida.** Dados da própria conta.

**200 OK**: `{ "nome": "Ana Souza", "email": "ana@exemplo.com" }`

**401 Unauthorized**: ver abaixo. Os demais métodos respondem 405.

---

## Erros de autenticação (todas as rotas protegidas)

| Situação | Status | Corpo (principal) |
|---|---|---|
| Sem cabeçalho `Authorization` | 401 | `{"detail": "As credenciais de autenticação não foram fornecidas."}` |
| Credencial vencida | 401 | `{"code": "token_not_valid", "detail": "...", "messages": [{"message": "Token expirado", ...}]}` |
| Credencial adulterada ou inválida | 401 | `{"code": "token_not_valid", ...}` |
| Conta desativada | 401 | `{"code": "user_inactive", "detail": "Usuário está inativo"}` |

As respostas 401 trazem `WWW-Authenticate: Bearer realm="api"`.

**Regra para a interface (US-26)**: 401 com `code == "token_not_valid"` → chamar `renovar` uma
vez e repetir a requisição; se a renovação responder 401 → levar ao login. 401 sem `code`
(credencial ausente) → levar ao login.

## Rotas públicas (FR-010)

`GET /api/health/`, `POST /api/usuarios/` (cadastro), `POST /api/auth/entrar/` e
`POST /api/auth/renovar/`. **Todas as outras** exigem credencial de acesso.

## Variáveis de ambiente novas

| Variável | Padrão | Descrição |
|---|---|---|
| `GRANA_SESSAO_ACESSO_MINUTOS` | `30` | Duração da credencial de acesso (inteiro ≥ 1) |
| `GRANA_SESSAO_RENOVACAO_DIAS` | `7` | Duração da credencial de renovação (inteiro ≥ 1) |
| `GRANA_LOGIN_TENTATIVAS_POR_MINUTO` | `10` | Tentativas de login por minuto por dispositivo (inteiro ≥ 1) |
| `GRANA_PROXY_CONFIAVEL` | `frontend` | Host do proxy cujo `X-Forwarded-For` é aceito para identificar o dispositivo |

Complementa [../../001-infra-docker/contracts/environment.md](../../001-infra-docker/contracts/environment.md).
