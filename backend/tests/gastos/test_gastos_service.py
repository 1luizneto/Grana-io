"""Regras de gastos que cruzam modelos (specs/008-lancar-gastos/research.md, R-03)."""

import pytest

from gastos.models import MesReferencia
from gastos.services.gastos import RegraViolada, exigir_mes_aberto

pytestmark = pytest.mark.django_db

MES_FECHADO = "O mês {} está fechado. Reabra o mês para alterar os gastos."


# Mês fechado (FR-008)


def test_mes_aberto_passa(usuario):
    exigir_mes_aberto(MesReferencia.objects.create(dono=usuario, mes=10, ano=2026))


def test_mes_fechado_e_recusado(usuario):
    fechado = MesReferencia.objects.create(dono=usuario, mes=10, ano=2026, fechado=True)

    with pytest.raises(RegraViolada) as erro:
        exigir_mes_aberto(fechado)

    assert str(erro.value) == MES_FECHADO.format("10/2026")


def test_acusa_o_primeiro_mes_fechado(usuario):
    aberto = MesReferencia.objects.create(dono=usuario, mes=9, ano=2026)
    fechado = MesReferencia.objects.create(dono=usuario, mes=11, ano=2026, fechado=True)

    with pytest.raises(RegraViolada, match="11/2026"):
        exigir_mes_aberto(aberto, None, fechado)


def test_ignora_none():
    exigir_mes_aberto(None)
