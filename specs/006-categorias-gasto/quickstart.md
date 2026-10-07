# Quickstart de Validação: Categorias de Gasto

**Feature**: `006-categorias-gasto` | **Plano**: [plan.md](plan.md)

Contratos: [api-categorias.md](contracts/api-categorias.md) e
[tela-categorias.md](contracts/tela-categorias.md).

## Pré-requisitos

- Sistema no ar: `docker compose up -d --wait`. A migration nova roda sozinha na subida.
- Uma conta existente (ex.: `ana@exemplo.com` / `uma-senha-boa-2026`), criada antes desta entrega.

## Cenários

### S1 — Suíte completa (constituição, Princípio IV)

```bash
sh testar.sh
```

**Esperado**: backend e interface verdes, incluindo o kit de isolamento aplicado às categorias.

### S2 — Contas antigas recebem as padrão (US1; FR-002; SC-001)

```bash
docker compose exec -T db psql -U grana -d grana -c "select u.email, count(c.id) from accounts_usuario u left join gastos_categoria c on c.dono_id = u.id group by u.email order by u.email;"
```

**Esperado**: toda conta com exatamente 7 categorias. Reinicie o backend
(`docker compose restart backend`) e rode de novo: continua 7 (sem duplicar).

### S3 — Conta nova já nasce com as padrão (US1; FR-001)

Pela tela, crie uma conta nova em `/cadastro` e abra "Categorias" no menu.

**Esperado**: as 7 padrão, em ordem alfabética (Alimentação, Educação, Lazer, Moradia, Outros,
Saúde, Transporte), cada uma com a sua cor.

### S4 — Criar, repetir, renomear e trocar cor pela tela (US2, US3, US5; SC-002, SC-004)

Marque o tempo.

1. Crie "Pets" escolhendo "Verde" → aparece na posição alfabética, com amostra verde.
2. Tente criar "pets" → "Já existe uma categoria com este nome." ao lado do campo; o texto continua
   no campo.
3. Crie "Assinaturas" sem escolher cor → recebe uma cor que nenhuma outra usa.
4. Edite "Lazer" para "Lazer e viagens" → novo nome, mesma cor.
5. Troque a cor de "Saúde" para "Índigo" → amostra muda.
6. Exclua "Pets": cancele a confirmação (continua na lista); exclua de novo e confirme (some).

**Esperado**: todos os passos como descrito; do 1 ao 6 em até 2 minutos (SC-004).

### S5 — Isolamento (FR-009; SC-005)

Com duas contas (Ana e Bia), cada uma com "Pets": cada uma vê só a sua. Pela API, com a sessão de
Ana, `GET /api/categorias/<id da Pets da Bia>/` → `404 {"detail": "Não encontrado."}`. (Coberto
também pelo kit de isolamento no S1.)

### S6 — Teclado e tela estreita (FR-013, FR-014)

Em 360 px de largura: sem rolagem horizontal; com Tab e setas, criar uma categoria escolhendo a cor
só pelo teclado.

### S7 — Paleta pela API (FR-007, FR-013)

`GET /api/categorias/cores/` com sessão → 12 cores com `codigo`, `nome` e `hex`; `POST` com
`"cor": "dourado"` → `{"cor": ["Escolha uma das cores disponíveis."]}`.
