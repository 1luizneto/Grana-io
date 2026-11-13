# Quickstart de Validação: Gastos Fixos

**Feature**: `010-gastos-fixos` | Contratos: [api-fixos.md](contracts/api-fixos.md),
[tela-fixos.md](contracts/tela-fixos.md)

## Pré-requisitos

Sistema no ar (`docker compose up -d --wait`); uma conta de teste com as categorias padrão, sem
meses.

## Cenários

### S1 — Suítes

`sh testar.sh` → verde.

### S2 — Cadastrar (US1)

Na tela "Gastos fixos": Aluguel, "1.500,00", dia 5, Moradia, início 11/2026 → "Gasto fixo
cadastrado." e o item "dia 5", "desde 11/2026". Dia "32" → "Informe um dia de 1 a 31.". Fim
10/2026 → mensagem de fim antes do início.

### S3 — Repetir todo mês (US1)

Criar 11/2026 na tela do mês (o Aluguel entra no dia 05/11, marcado "fixo"); lançar "Internet",
"99,90", 30/11/2026, com "Repetir todo mês" → "Gasto lançado e cadastrado como fixo."; a tela
"Gastos fixos" mostra Internet, dia 30, desde 11/2026.

### S4 — Gerar ao criar o mês (US2)

Criar 12/2026 → Aluguel em 05/12 e Internet em 30/12, ambos "fixo"; total R$ 1.599,90. Criar
02/2027 → Internet em 28/02.

### S5 — Só para frente (US3)

Mudar o Aluguel para "1.600,00" → 12/2026 continua R$ 1.500,00; criar 01/2027 → R$ 1.600,00.
Desativar a Internet; criar 03/2027 → sem Internet. Excluir o Aluguel (confirmando) → os gastos
de Aluguel continuam nos meses.

### S6 — Isolamento e limpeza

Com outra conta, `GET /api/fixos/<id do Aluguel>/` → 404. Excluir gastos, meses e fixos de teste.
