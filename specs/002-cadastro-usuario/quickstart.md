# Quickstart de Validação: Cadastro de Usuário

**Feature**: `002-cadastro-usuario` | **Plano**: [plan.md](plan.md)

Roteiro de ponta a ponta da feature. O contrato está em
[contracts/api-cadastro.md](contracts/api-cadastro.md) e o modelo em
[data-model.md](data-model.md).

## Pré-requisitos

- Ambiente da spec 001 funcionando (`docker compose up -d --wait`).
- **Uma única vez**, depois de implementar o modelo de usuário: `docker compose down -v` e
  `docker compose up -d --wait`, para recriar o banco com o novo `AUTH_USER_MODEL`
  ([research R-02](research.md)).
- Os exemplos usam `curl` no Git Bash ou Linux. No PowerShell, use `curl.exe` e aspas simples em
  volta do JSON.

Atalho usado abaixo:

```bash
cadastrar() { curl -s -w " [%{http_code}]\n" -H "Content-Type: application/json" -d "$1" http://localhost:8000/api/usuarios/; }
```

## Cenários

### Q1 — Cadastro válido (US1; FR-001, FR-003, FR-009, FR-010, FR-011)

```bash
cadastrar '{"nome":"  Ana Souza ","email":" Ana@Exemplo.com ","senha":"uma-senha-boa-2026","confirmacao_senha":"uma-senha-boa-2026"}'
```

**Esperado**: `{"nome":"Ana Souza","email":"ana@exemplo.com"} [201]`, sem `id`, senha nem token.

### Q2 — Senha protegida e conta sem privilégios (US1; FR-007, FR-011; SC-003)

```bash
docker compose exec -T db psql -U grana -d grana -c "select email, nome, left(password, 25) as senha, is_active, is_staff, is_superuser from accounts_usuario;"
```

**Esperado**: `password` começa com `pbkdf2_sha256$` e não contém `uma-senha-boa-2026`.
`is_active = t`, `is_staff = f`, `is_superuser = f`.

### Q3 — E-mail duplicado (US2; FR-004; SC-002)

```bash
cadastrar '{"nome":"Outra","email":"ANA@exemplo.com","senha":"outra-senha-boa-9","confirmacao_senha":"outra-senha-boa-9"}'
cadastrar '{"nome":"Outra","email":"  ana@exemplo.com  ","senha":"outra-senha-boa-9","confirmacao_senha":"outra-senha-boa-9"}'
```

**Esperado**: as duas respostas são `{"email":["Já existe uma conta com este e-mail."]} [400]`, e
continua existindo 1 conta com esse e-mail.

### Q4 — Validações por campo (US3; FR-002, FR-005, FR-006, FR-008; SC-004, SC-005)

| Envio | Esperado (400) |
|---|---|
| `{}` | `nome`, `email`, `senha` e `confirmacao_senha` com "Este campo é obrigatório." |
| `nome` = `"   "` | `nome`: "Este campo é obrigatório." |
| `email` = `"ana@"` | `email`: "Insira um endereço de email válido." |
| senha e confirmação diferentes | `confirmacao_senha`: "As senhas não conferem." |
| senha `"abc12"` | `senha`: menciona o mínimo de 8 caracteres |
| senha `"98765432109"` | `senha`: "Esta senha é inteiramente numérica." |
| senha `"senha123"` e `"mudar123"` | `senha`: "Esta senha é muito comum." |
| nome `"Carlos"`, e-mail `carlos@x.com`, senha `"carlos@x.com"` | `senha`: parecida demais com os dados pessoais |
| vários problemas juntos | todas as mensagens na mesma resposta |

Depois de todos os envios, nenhuma conta nova foi criada (conferir a contagem com o comando do Q2).

### Q5 — Cadastro fechado (FR-012)

1. No `.env`, defina `GRANA_CADASTRO_ABERTO=0` e rode `docker compose up -d --wait`.
2. Envie um cadastro **válido**.
   **Esperado**: `{"detail":"O cadastro de novas contas está desativado neste sistema."} [403]`,
   e nenhuma conta criada.
3. Volte para `GRANA_CADASTRO_ABERTO=1` (ou apague a linha) e suba de novo. **Esperado**: o
   cadastro volta a funcionar, e as contas existentes continuam intactas.

### Q6 — Rota não lista usuários (FR-013)

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/usuarios/
```

**Esperado**: `405`.

### Q7 — Senha fora das páginas de erro e dos logs (FR-007)

1. `docker compose logs backend | grep -c "uma-senha-boa-2026"`. **Esperado**: `0`.
2. A proteção da página de erro de desenvolvimento (`sensitive_post_parameters`) é coberta por
   teste automatizado ([research R-06](research.md)).

### Q8 — Suíte automatizada (Princípio IV)

```bash
docker compose run --rm backend pytest
```

**Esperado**: todos os testes aprovados, incluindo os de model/manager, validadores, service
(com a corrida simulada de e-mail duplicado) e API do cadastro, além da guarda de migrations
pendentes.

### Q9 — Administrador por comando (spec, Assumptions)

```bash
docker compose exec backend python manage.py createsuperuser
```

**Esperado**: o comando pede **e-mail** e **nome** (não "username") e cria a conta com
`is_staff = t` e `is_superuser = t`.

## Critério de encerramento

Q1 a Q9 passam e a suíte (Q8) está verde.
