# Quickstart de Validação: Gastos

**Feature**: `008-lancar-gastos` | **Plano**: [plan.md](plan.md)

Esta spec só tem API (a tela é a US-27). Contrato: [api-gastos.md](contracts/api-gastos.md).

## Pré-requisitos

- Sistema no ar: `docker compose up -d --wait` (a migration roda sozinha).
- Duas contas (`ana@exemplo.com` e `bia@exemplo.com`, senha `uma-senha-boa-2026`), ambas com as
  categorias padrão.
- No Git Bash, `MSYS_NO_PATHCONV=1`; no PowerShell, `curl.exe`.

```bash
API=http://localhost:8000/api
entrar() { curl -s -H "Content-Type: application/json" -d "{\"email\":\"$1\",\"senha\":\"uma-senha-boa-2026\"}" $API/auth/entrar/ | py -c "import sys,json;print(json.load(sys.stdin)['acesso'])"; }
ANA=$(entrar ana@exemplo.com); BIA=$(entrar bia@exemplo.com)
req() { curl -s -w " [%{http_code}]\n" -H "Authorization: Bearer $1" -H "Content-Type: application/json" "${@:2}"; }
```

Crie o mês 10/2026 da Ana (`MES`) e anote os ids das categorias Alimentação (`ALI`), Transporte
(`TRA`), Lazer (`LAZ`) e Outros (`OUT`) em `GET $API/categorias/`.

## Cenários

### S1 — Suíte completa

`sh testar.sh` → backend e interface verdes, com o kit de isolamento aplicado aos gastos.

### S2 — Lançar e recusar (US1; FR-001 a FR-004)

```bash
req $ANA -d "{\"descricao\":\"Mercado\",\"valor\":\"150.30\",\"data\":\"2026-10-05\",\"mes\":$MES,\"categoria\":$ALI,\"forma_pagamento\":\"pix\"}" $API/gastos/
req $ANA -d "{\"descricao\":\"X\",\"valor\":\"0\",\"data\":\"2026-10-05\",\"mes\":$MES,\"categoria\":$ALI}" $API/gastos/
req $ANA -d "{\"descricao\":\"X\",\"valor\":\"10\",\"data\":\"2026-11-05\",\"mes\":$MES,\"categoria\":$ALI}" $API/gastos/
req $ANA -d "{\"descricao\":\"X\",\"valor\":\"10.555\",\"data\":\"2026-10-05\",\"mes\":$MES,\"categoria\":$ALI}" $API/gastos/
```

**Esperado**: 201 com `"valor": "150.30"`; 400 "Informe um valor maior que zero."; 400 "A data
precisa estar dentro de 10/2026." (conferida só quando os demais campos estão válidos); 400 "Use
no máximo 2 casas decimais.".

### S3 — Lista e totais (US2; FR-005, FR-006)

Lance também Feira 49,70 (Alimentação, 2026-10-02) e Uber 23,45 (Transporte, 2026-10-05).

```bash
req $ANA "$API/gastos/?mes=$MES"
req $ANA $API/meses/$MES/totais/
```

**Esperado**: Feira, Mercado, Uber (por data e lançamento); total `"223.45"`, Alimentação
`"200.00"` (2), Transporte `"23.45"` (1).

### S4 — Corrigir, excluir e mês fechado (US3; FR-007, FR-008)

Com o id do Uber em `UBER`:

```bash
req $ANA -X PATCH -d '{"valor":"25.00"}' $API/gastos/$UBER/
req $ANA -X PATCH -d '{"fechado":true}' $API/meses/$MES/
req $ANA -X PATCH -d '{"valor":"26.00"}' $API/gastos/$UBER/
req $ANA -X DELETE $API/gastos/$UBER/
req $ANA -X PATCH -d '{"fechado":false}' $API/meses/$MES/
req $ANA -X DELETE $API/gastos/$UBER/
```

**Esperado**: 200 com `"25.00"`; 200; 400 e 400 com "O mês 10/2026 está fechado. Reabra o mês
para alterar os gastos."; 200; 204.

### S5 — Proteger o histórico (US4; FR-009, FR-010)

Lance um gasto em Lazer (`LAZ`).

```bash
req $ANA -X DELETE $API/meses/$MES/
req $ANA -X DELETE $API/categorias/$LAZ/
req $ANA -X DELETE "$API/categorias/$LAZ/?mover_para=$LAZ"
req $ANA -X DELETE "$API/categorias/$LAZ/?mover_para=$OUT"
req $ANA "$API/gastos/?categoria=$OUT"
```

**Esperado**: 400 "Exclua ou mova os gastos antes de excluir o mês."; 400 "Esta categoria tem
gastos..."; 400 no campo `mover_para`; 204; o gasto de Lazer agora em Outros.

### S6 — Isolamento (FR-012)

```bash
req $BIA $API/gastos/<id de um gasto da Ana>/
req $BIA "$API/gastos/?mes=$MES"
req $BIA $API/meses/$MES/totais/
```

**Esperado**: 404 `{"detail": "Não encontrado."}`; `[]`; 404.

### S7 — Limpeza

Exclua os gastos de teste, o mês 10/2026 da Ana e recrie a categoria Lazer (rosa) da Ana, para o
banco local voltar ao estado anterior.
