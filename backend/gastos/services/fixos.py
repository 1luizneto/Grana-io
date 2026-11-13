"""Gastos fixos (US-07b; specs/010-gastos-fixos/research.md, R-03 e R-04)."""

import calendar
from datetime import date

from django.db.models import Q

from gastos.models import Gasto, GastoFixo


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


def gerar_gastos_fixos(mes):
    """Lança no mês recém-criado um gasto para cada fixo ativo do período (FR-004).

    O vencimento que não existe no mês (dia 31 em novembro) cai no último dia. Meses que já
    existiam nunca passam por aqui (FR-005). Quem chama garante a transação.
    """
    primeiro_dia = date(mes.ano, mes.mes, 1)
    ultimo_dia = calendar.monthrange(mes.ano, mes.mes)[1]
    fixos = GastoFixo.objects.do_dono(mes.dono).filter(
        Q(fim__isnull=True) | Q(fim__gte=primeiro_dia), ativo=True, inicio__lte=primeiro_dia
    )
    Gasto.objects.bulk_create(
        Gasto(
            dono=mes.dono,
            mes=mes,
            fixo=fixo,
            descricao=fixo.descricao,
            valor=fixo.valor,
            categoria_id=fixo.categoria_id,
            forma_pagamento=fixo.forma_pagamento,
            data=primeiro_dia.replace(day=min(fixo.dia_vencimento, ultimo_dia)),
        )
        for fixo in fixos
    )
