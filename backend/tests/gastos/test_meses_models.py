"""Model MesReferencia (FR-001 a FR-003; specs/007-mes-referencia/data-model.md)."""

import pytest
from django.db import IntegrityError, models, transaction

from core.models import OwnedModel
from gastos.models import MesReferencia

pytestmark = pytest.mark.django_db


def _mes(dono, mes, ano, **extra):
    return MesReferencia.objects.create(dono=dono, mes=mes, ano=ano, **extra)


def test_mes_tem_dono():
    assert issubclass(MesReferencia, OwnedModel)


def test_campos():
    assert isinstance(MesReferencia._meta.get_field("mes"), models.PositiveSmallIntegerField)
    assert isinstance(MesReferencia._meta.get_field("ano"), models.PositiveSmallIntegerField)
    fechado = MesReferencia._meta.get_field("fechado")
    assert isinstance(fechado, models.BooleanField)
    assert fechado.default is False


def test_nasce_aberto(usuario):
    assert _mes(usuario, 10, 2026).fechado is False


def test_mes_repetido_na_mesma_conta(usuario):
    _mes(usuario, 10, 2026)

    with pytest.raises(IntegrityError, match="gastos_mes_unico_por_dono"), transaction.atomic():
        _mes(usuario, 10, 2026)

    assert MesReferencia.objects.count() == 1


def test_mesmo_mes_em_contas_diferentes(usuario, outro_usuario):
    _mes(usuario, 10, 2026)
    _mes(outro_usuario, 10, 2026)

    assert MesReferencia.objects.count() == 2


@pytest.mark.parametrize("mes", [0, 13])
def test_mes_fora_da_faixa(usuario, mes):
    with pytest.raises(IntegrityError, match="gastos_mes_mes_valido"), transaction.atomic():
        _mes(usuario, mes, 2026)


@pytest.mark.parametrize("ano", [1999, 2101])
def test_ano_fora_da_faixa(usuario, ano):
    with pytest.raises(IntegrityError, match="gastos_mes_ano_valido"), transaction.atomic():
        _mes(usuario, 10, ano)


def test_limites_aceitos(usuario):
    _mes(usuario, 1, 2000)
    _mes(usuario, 12, 2100)

    assert MesReferencia.objects.count() == 2


def test_ordem_cronologica(usuario):
    for mes, ano in [(3, 2027), (12, 2026), (1, 2026)]:
        _mes(usuario, mes, ano)

    rotulos = [str(m) for m in MesReferencia.objects.do_dono(usuario)]

    assert rotulos == ["01/2026", "12/2026", "03/2027"]


def test_rotulo(usuario):
    mes = _mes(usuario, 3, 2027)

    assert mes.rotulo == "03/2027"
    assert str(mes) == "03/2027"
