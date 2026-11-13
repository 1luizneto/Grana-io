# Quickstart de Validação: Tela do Mês

**Feature**: `009-tela-mes` | **Plano**: [plan.md](plan.md) | **Contrato**: [tela-mes.md](contracts/tela-mes.md)

## Pré-requisitos

- Sistema no ar: `docker compose up -d --wait`; interface em http://localhost:5173.
- Uma conta nova criada pela tela de cadastro (vem com as 7 categorias padrão).

## Cenários

### S1 — Suítes

`sh testar.sh` → backend e interface verdes.

### S2 — Primeiro mês (US1)

Entrar e abrir "Gastos do mês". **Esperado**: "Nenhum mês criado. Crie o primeiro abaixo."; criar
o mês de hoje → "Mês criado." e o endereço `/meses/<id>`.

### S3 — Lançar e totais (US2)

Lançar "Mercado", "150,30", Alimentação, Pix; depois "Feira", "49,70", Alimentação; "Uber",
"23,45", Transporte. **Esperado**: "Gasto lançado." a cada um; tabela com os 3; "Total do mês"
R$ 223,45; Alimentação R$ 200,00 (2 gastos), Transporte R$ 23,45 (1 gasto). Lançar com valor "0" →
"Informe um valor maior que zero." ao lado do campo. Medir o tempo de um lançamento (SC-001).

### S4 — Corrigir e excluir (US3)

Editar o Uber para "25,00" → "Gasto atualizado." e total R$ 225,00. Excluir a Feira cancelando
(fica) e confirmando ("Gasto excluído.", total R$ 175,30).

### S5 — Filtrar e ordenar (US4)

Filtrar por Transporte → só o Uber; "Maior valor" → Mercado antes do Uber.

### S6 — Fechar, reabrir, excluir mês (US5)

Fechar → aviso de mês fechado e formulário desabilitado; reabrir. Criar o mês seguinte e excluí-lo
(confirmando) → volta a outro mês. Tentar excluir o mês com gastos → "Exclua ou mova os gastos
antes de excluir o mês.".

### S7 — Excluir categoria com destino (US6)

Lançar um gasto em Lazer; em "Categorias", "Excluir Lazer" → painel com "Mover os gastos para"
(Outros); confirmar; na tela do mês, o gasto aparece em Outros.

### S8 — Tela estreita e teclado (FR-013)

Em 360 px: sem rolagem horizontal; tabela em cartões. Lançar um gasto só pelo teclado.

### S9 — Limpeza

Excluir os gastos e os meses de teste (a conta de teste pode ficar).
