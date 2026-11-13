"""Gastos fixos (US-07b; specs/010-gastos-fixos/research.md, R-03 e R-04)."""

from gastos.models import GastoFixo


def criar_fixo_do_gasto(gasto):
    """Cadastra ``gasto`` como fixo a partir do mês dele, com vencimento no dia da data, e liga o
    gasto ao fixo ("Repetir todo mês"). Quem chama garante a transação."""
    fixo = GastoFixo.objects.create(
        dono=gasto.dono,
        descricao=gasto.descricao,
        valor=gasto.valor,
        categoria=gasto.categoria,
        forma_pagamento=gasto.forma_pagamento,
        dia_vencimento=gasto.data.day,
        inicio=gasto.data.replace(day=1),
    )
    gasto.fixo = fixo
    gasto.save(update_fields=["fixo"])
    return fixo
