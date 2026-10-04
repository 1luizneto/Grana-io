# Quickstart de Validação: Login e Logout

**Feature**: `003-login-logout` | **Plano**: [plan.md](plan.md)

Roteiro de ponta a ponta. O contrato está em [contracts/api-sessao.md](contracts/api-sessao.md).

## Pré-requisitos

- Sistema no ar (`docker compose up -d --build --wait`), com as migrations do `token_blacklist`
  aplicadas automaticamente na subida.
- Uma conta criada pelo cadastro (spec 002). Exemplo: `ana@exemplo.com` / `uma-senha-boa-2026`.
- Os exemplos usam `curl` no Git Bash ou Linux, com `MSYS_NO_PATHCONV=1` no Git Bash. No
  PowerShell, use `curl.exe`.

```bash
API=http://localhost:8000/api
post() { curl -s -w " [%{http_code}]\n" -H "Content-Type: application/json" "$@"; }
```

## Cenários

### S1 — Entrar (US1; FR-001, FR-002, FR-005)

```bash
post -d '{"email":" ANA@Exemplo.com ","senha":"uma-senha-boa-2026"}' $API/auth/entrar/
```

**Esperado**: 200 com `acesso`, `renovacao` e `usuario: {"nome": ..., "email": "ana@exemplo.com"}`.
Guarde os valores em `ACESSO` e `RENOVACAO`. A coluna `last_login` da conta foi preenchida:

```bash
docker compose exec -T db psql -U grana -d grana -c "select email, last_login from accounts_usuario;"
```

### S2 — Própria conta (US1; US3; FR-010 a FR-012)

```bash
curl -s -w " [%{http_code}]\n" -H "Authorization: Bearer $ACESSO" $API/usuarios/eu/
curl -s -w " [%{http_code}]\n" $API/usuarios/eu/
curl -s -w " [%{http_code}]\n" -H "Authorization: Bearer abc.def.ghi" $API/usuarios/eu/
```

**Esperado**: 200 com nome e e-mail; 401 "As credenciais de autenticação não foram fornecidas.";
401 com `"code": "token_not_valid"`.

### S3 — Credenciais inválidas idênticas (US2; FR-003, FR-004; SC-002)

```bash
post -d '{"email":"ninguem@exemplo.com","senha":"qualquer-coisa-1"}' $API/auth/entrar/
post -d '{"email":"ana@exemplo.com","senha":"senha-errada-123"}' $API/auth/entrar/
post -d '{}' $API/auth/entrar/
```

**Esperado**: as duas primeiras respostas são idênticas, `{"detail":"E-mail ou senha incorretos."}
[401]`; a terceira é 400 com "Este campo é obrigatório." em `email` e `senha`.

### S4 — Renovar (US4; FR-007, FR-008)

```bash
post -d "{\"renovacao\":\"$RENOVACAO\"}" $API/auth/renovar/
post -d "{\"renovacao\":\"$RENOVACAO\"}" $API/auth/renovar/
```

**Esperado**: a primeira dá 200 com um par novo (guarde o novo `renovacao`); a segunda, com a
credencial antiga, dá 401 "Sessão expirada ou encerrada. Entre novamente.".

### S5 — Sair (US5; FR-009; SC-004)

1. Entre duas vezes (S1), simulando dois dispositivos: pares A e B.
2. `post -H "Authorization: Bearer $ACESSO_A" -d "{\"renovacao\":\"$RENOVACAO_A\"}" $API/auth/sair/`
   **Esperado**: 204.
3. Renovar com `RENOVACAO_A`. **Esperado**: 401.
4. Renovar com `RENOVACAO_B`. **Esperado**: 200 (o outro dispositivo segue conectado).
5. Com a conta de outra pessoa (crie `bia@exemplo.com`), tentar sair usando o `ACESSO` da Bia e a
   `RENOVACAO_B` da Ana. **Esperado**: 400 "Sessão inválida ou já encerrada.", e a `RENOVACAO_B`
   continua renovando.

### S6 — Conta desativada (FR-014)

```bash
docker compose exec -T backend python manage.py shell -v 0 -c "from accounts.models import Usuario; Usuario.objects.filter(email='ana@exemplo.com').update(is_active=False)"
```

Em seguida:
- `GET /usuarios/eu/` com o acesso ainda não vencido: 401 com `"code": "user_inactive"`;
- renovar: 401;
- entrar: 401 "E-mail ou senha incorretos.".

Reative a conta com o mesmo comando e `is_active=True`.

### S7 — Limite de tentativas (FR-015; SC-007)

```bash
for i in $(seq 1 11); do post -d '{"email":"ana@exemplo.com","senha":"senha-errada-123"}' http://localhost:5173/api/auth/entrar/; done
```

**Esperado**: as 10 primeiras dão 401 e a 11ª dá `{"detail":"Muitas tentativas. Tente novamente
em instantes."} [429]`, pela interface (porta 5173, via proxy). Depois de 1 minuto, o login volta a
ser aceito.

- **No Docker Desktop (Windows/macOS)**: um login logo em seguida pela porta 8000, ou por outro
  dispositivo, **também** recebe 429, porque todos chegam com o mesmo endereço e compartilham o
  limite. É a limitação documentada na spec (Edge Cases).
- **No Linux (Docker Engine)**: um login de outro dispositivo da rede é contado à parte.

Em qualquer ambiente, os testes automatizados cobrem a contagem por endereço e a garantia de que
um `X-Forwarded-For` falso na porta 8000 não burla o limite.

### S8 — Rotas públicas continuam públicas (FR-010; SC-003)

`GET /api/health/` → 200 e `POST /api/usuarios/` → 201 ou 400, os dois sem credencial.

### S9 — Nada de segredos nos logs (FR-013; SC-006)

```bash
docker compose logs backend | grep -cE "uma-senha-boa-2026|senha-errada-123|eyJ"
```

**Esperado**: `0`. `eyJ` é o início de qualquer credencial JWT.

### S10 — Suíte (Princípio IV)

`docker compose run --rm backend pytest` → todos os testes aprovados.

## Critério de encerramento

S1 a S10 passam e a suíte está verde.
