"""Model Gasto (specs/008-lancar-gastos/data-model.md)."""

from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError, models, transaction
from django.db.models import RestrictedError

from accounts.models import Usuario
from core.models import OwnedModel
from gastos.models import FORMAS_PAGAMENTO, Categoria, Gasto, MesReferencia

pytestmark = pytest.mark.django_db


def _gasto(dono, valor="10.00", data=date(2026, 10, 5), descricao="Mercado", **extra):
    mes, _ = MesReferencia.objects.get_or_create(dono=dono, mes=10, ano=2026)
    categoria, _ = Categoria.objects.get_or_create(
        dono=dono, nome="Alimentação", defaults={"cor": "laranja"}
    )
    return Gasto.objects.create(
        dono=dono, mes=mes, categoria=categoria, descricao=descricao, valor=Decimal(valor),
        data=data, **extra,
    )


def test_gasto_tem_dono():
    assert issubclass(Gasto, OwnedModel)


def test_campos():
    descricao = Gasto._meta.get_field("descricao")
    valor = Gasto._meta.get_field("valor")
    forma = Gasto._meta.get_field("forma_pagamento")

    assert descricao.max_length == 100
    assert isinstance(valor, models.DecimalField)
    assert (valor.max_digits, valor.decimal_places) == (12, 2)
    assert forma.max_length == 10
    assert forma.blank is True
    assert forma.default == ""
    assert list(forma.choices) == FORMAS_PAGAMENTO
    assert [codigo for codigo, _ in FORMAS_PAGAMENTO] == ["dinheiro", "debito", "credito", "pix"]


@pytest.mark.parametrize("valor", ["0", "-1.00"])
def test_valor_precisa_ser_positivo(usuario, valor):
    with pytest.raises(IntegrityError, match="gastos_gasto_valor_positivo"), transaction.atomic():
        _gasto(usuario, valor=valor)


def test_mes_com_gasto_nao_se_exclui(usuario):
    gasto = _gasto(usuario)

    with pytest.raises(RestrictedError):
        gasto.mes.delete()

    assert Gasto.objects.filter(pk=gasto.pk).exists()


def test_categoria_com_gasto_nao_se_exclui(usuario):
    gasto = _gasto(usuario)

    with pytest.raises(RestrictedError):
        gasto.categoria.delete()

    assert Gasto.objects.filter(pk=gasto.pk).exists()


def test_excluir_a_conta_apaga_tudo_dela(usuario, outro_usuario):
    _gasto(usuario)
    da_bia = _gasto(outro_usuario)

    Usuario.objects.filter(pk=usuario.pk).delete()

    assert list(Gasto.objects.all()) == [da_bia]
    assert MesReferencia.objects.count() == 1
    assert Categoria.objects.count() == 1


def test_ordem_por_data_e_lancamento(usuario):
    terceiro = _gasto(usuario, descricao="C", data=date(2026, 10, 9))
    primeiro = _gasto(usuario, descricao="A", data=date(2026, 10, 2))
    segundo = _gasto(usuario, descricao="B", data=date(2026, 10, 9))

    assert list(Gasto.objects.do_dono(usuario)) == [primeiro, terceiro, segundo]


def test_str(usuario):
    assert str(_gasto(usuario, descricao="Feira")) == "Feira"
