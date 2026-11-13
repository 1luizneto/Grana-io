"""Model GastoFixo e a origem Gasto.fixo (specs/010-gastos-fixos/data-model.md)."""

from datetime import date
from decimal import Decimal

import pytest
from django.db import IntegrityError, models, transaction
from django.db.models import RestrictedError

from accounts.models import Usuario
from core.models import OwnedModel
from gastos.models import FORMAS_PAGAMENTO, Categoria, Gasto, GastoFixo, MesReferencia

pytestmark = pytest.mark.django_db


def _categoria(dono):
    return Categoria.objects.get_or_create(dono=dono, nome="Moradia", defaults={"cor": "azul"})[0]


def _fixo(dono, **mudancas):
    dados = {
        "descricao": "Aluguel",
        "valor": Decimal("1500.00"),
        "categoria": _categoria(dono),
        "dia_vencimento": 5,
        "inicio": date(2026, 11, 1),
        **mudancas,
    }
    return GastoFixo.objects.create(dono=dono, **dados)


def test_fixo_tem_dono():
    assert issubclass(GastoFixo, OwnedModel)


def test_campos():
    campo = GastoFixo._meta.get_field

    assert campo("descricao").max_length == 100
    assert (campo("valor").max_digits, campo("valor").decimal_places) == (12, 2)
    assert list(campo("forma_pagamento").choices) == FORMAS_PAGAMENTO
    assert campo("forma_pagamento").default == ""
    assert isinstance(campo("dia_vencimento"), models.PositiveSmallIntegerField)
    assert isinstance(campo("inicio"), models.DateField)
    assert campo("fim").null is True
    assert campo("ativo").default is True


def test_padroes(usuario):
    fixo = _fixo(usuario)

    assert fixo.ativo is True
    assert fixo.fim is None
    assert fixo.forma_pagamento == ""


@pytest.mark.parametrize("valor", ["0", "-1.00"])
def test_valor_positivo(usuario, valor):
    with pytest.raises(IntegrityError, match="gastos_fixo_valor_positivo"), transaction.atomic():
        _fixo(usuario, valor=Decimal(valor))


@pytest.mark.parametrize("dia", [0, 32])
def test_dia_valido(usuario, dia):
    with pytest.raises(IntegrityError, match="gastos_fixo_dia_valido"), transaction.atomic():
        _fixo(usuario, dia_vencimento=dia)


def test_fim_antes_do_inicio(usuario):
    with (
        pytest.raises(IntegrityError, match="gastos_fixo_fim_depois_do_inicio"),
        transaction.atomic(),
    ):
        _fixo(usuario, fim=date(2026, 10, 1))


def test_fim_igual_ao_inicio(usuario):
    assert _fixo(usuario, fim=date(2026, 11, 1)).fim == date(2026, 11, 1)


def test_categoria_com_fixo_nao_se_exclui(usuario):
    fixo = _fixo(usuario)

    with pytest.raises(RestrictedError):
        fixo.categoria.delete()


def test_excluir_a_conta_apaga_os_fixos(usuario, outro_usuario):
    _fixo(usuario)
    da_bia = _fixo(outro_usuario)

    Usuario.objects.filter(pk=usuario.pk).delete()

    assert list(GastoFixo.objects.all()) == [da_bia]


def test_gasto_guarda_a_origem_e_sobrevive_ao_fixo(usuario):
    fixo = _fixo(usuario)
    mes = MesReferencia.objects.create(dono=usuario, mes=11, ano=2026)
    sem_origem = Gasto.objects.create(
        dono=usuario, mes=mes, categoria=fixo.categoria, descricao="Avulso",
        valor=Decimal("10.00"), data=date(2026, 11, 2),
    )
    gerado = Gasto.objects.create(
        dono=usuario, mes=mes, categoria=fixo.categoria, descricao="Aluguel",
        valor=Decimal("1500.00"), data=date(2026, 11, 5), fixo=fixo,
    )

    assert sem_origem.fixo is None
    fixo.delete()
    gerado.refresh_from_db()
    assert gerado.fixo is None


def test_ordem_por_dia_e_cadastro(usuario):
    dia_10 = _fixo(usuario, descricao="Internet", dia_vencimento=10)
    dia_5_a = _fixo(usuario, descricao="Aluguel")
    dia_5_b = _fixo(usuario, descricao="Condomínio")

    assert list(GastoFixo.objects.do_dono(usuario)) == [dia_5_a, dia_5_b, dia_10]


def test_str(usuario):
    assert str(_fixo(usuario)) == "Aluguel"
