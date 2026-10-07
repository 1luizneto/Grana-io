# Quickstart de Validação: Mês de Referência

**Feature**: `007-mes-referencia` | **Plano**: [plan.md](plan.md)

Esta spec só tem API (a tela é a US-27). Contrato: [api-meses.md](contracts/api-meses.md).

## Pré-requisitos

- Sistema no ar: `docker compose up -d --wait` (a migration roda sozinha).
- Duas contas (ex.: `ana@exemplo.com` e `bia@exemplo.com`, senha `uma-senha-boa-2026`).
- No Git Bash, `MSYS_NO_PATHCONV=1`; no PowerShell, `curl.exe`.

```bash
API=http://localhost:8000/api
entrar() { curl -s -H "Content-Type: application/json" -d "{\"email\":\"$1\",\"senha\":\"uma-senha-boa-2026\"}" $API/auth/entrar/ | py -c "import sys,json;print(json.load(sys.stdin)['acesso'])"; }
ANA=$(entrar ana@exemplo.com); BIA=$(entrar bia@exemplo.com)
req() { curl -s -w " [%{http_code}]\n" -H "Authorization: Bearer $1" -H "Content-Type: application/json" "${@:2}"; }
```

## Cenários

### S1 — Suíte completa

```bash
sh testar.sh
```

**Esperado**: backend e interface verdes, com o kit de isolamento aplicado aos meses.

### S2 — Criar e repetir (US1; FR-001, FR-002)

```bash
req $ANA -d '{"mes":10,"ano":2026}' $API/meses/
req $ANA -d '{"mes":10,"ano":2026}' $API/meses/
req $BIA -d '{"mes":10,"ano":2026}' $API/meses/
req $ANA -d '{"mes":13,"ano":1999}' $API/meses/
```

**Esperado**: 201 com `"rotulo": "10/2026"` e `"fechado": false`; 400 "Este mês já foi criado.";
201 (Bia); 400 com "Informe um mês de 1 a 12." e "Informe um ano de 2000 a 2100.".

### S3 — Ordem cronológica (US2; FR-003)

```bash
req $ANA -d '{"mes":3,"ano":2027}' $API/meses/
req $ANA -d '{"mes":1,"ano":2026}' $API/meses/
req $ANA $API/meses/
```

**Esperado**: rótulos `01/2026`, `10/2026`, `03/2027`, nessa ordem.

### S4 — Fechar, excluir fechado, reabrir e excluir (US3, US4; FR-004, FR-005)

Com o `id` de 10/2026 da Ana em `ID`:

```bash
req $ANA -X PATCH -d '{"fechado":true}' $API/meses/$ID/
req $ANA -X DELETE $API/meses/$ID/
req $ANA -X PATCH -d '{"fechado":false}' $API/meses/$ID/
req $ANA -X DELETE $API/meses/$ID/
```

**Esperado**: 200 com `"fechado": true`; 400 "Reabra o mês antes de excluí-lo."; 200 com
`"fechado": false`; 204.

### S5 — Mês e ano não mudam; isolamento (FR-006, FR-008)

```bash
req $ANA -X PATCH -d '{"mes":11}' $API/meses/<id de um mês da Ana>/
req $ANA $API/meses/<id de um mês da Bia>/
```

**Esperado**: 400 "Não é possível alterar o mês ou o ano. Exclua o mês e crie de novo."; 404
`{"detail": "Não encontrado."}`.

### S6 — Limpeza

Exclua os meses criados nos cenários (abertos) para não deixar dados de teste no banco local.
