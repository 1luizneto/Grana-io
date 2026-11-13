"""Geração dos gastos fixos ao criar o mês (specs/010-gastos-fixos/research.md, R-03)."""

from datetime import date
from decimal import Decimal

import pytest

from gastos.models import Categoria, Gasto, GastoFixo, MesReferencia
from gastos.services.fixos import gerar_gastos_fixos

pytestmark = pytest.mark.django_db


def _fixo(dono, **mudancas):
    categoria = Categoria.objects.get_or_create(
        dono=dono, nome="Moradia", defaults={"cor": "azul"}
    )[0]
    dados = {
        "descricao": "Aluguel",
        "valor": Decimal("1500.00"),
        "categoria": categoria,
        "forma_pagamento": "pix",
        "dia_vencimento": 5,
        "inicio": date(2026, 11, 1),
        **mudancas,
    }
    return GastoFixo.objects.create(dono=dono, **dados)


def _gerar(dono, mes, ano):
    mes_ref = MesReferencia.objects.create(dono=dono, mes=mes, ano=ano)
    gerar_gastos_fixos(mes_ref)
    return list(Gasto.objects.filter(mes=mes_ref))


def test_gera_um_gasto_por_fixo_com_os_dados_do_fixo(usuario):
    fixo = _fixo(usuario)

    [gasto] = _gerar(usuario, 12, 2026)

    assert (gasto.descricao, gasto.valor, gasto.categoria, gasto.forma_pagamento) == (
        "Aluguel",
        Decimal("1500.00"),
        fixo.categoria,
        "pix",
    )
    assert gasto.data == date(2026, 12, 5)
    assert gasto.fixo == fixo
    assert gasto.dono == usuario


@pytest.mark.parametrize(
    "mes, ano, esperado",
    [(11, 2026, date(2026, 11, 30)), (2, 2027, date(2027, 2, 28)), (2, 2028, date(2028, 2, 29))],
)
def test_dia_que_nao_existe_vira_o_ultimo_dia(usuario, mes, ano, esperado):
    _fixo(usuario, dia_vencimento=31)

    [gasto] = _gerar(usuario, mes, ano)

    assert gasto.data == esperado


def test_nao_gera_desativado(usuario):
    _fixo(usuario, ativo=False)

    assert _gerar(usuario, 12, 2026) == []


def test_respeita_inicio_e_fim(usuario):
    _fixo(usuario, inicio=date(2026, 11, 1), fim=date(2027, 1, 1))

    assert len(_gerar(usuario, 10, 2026)) == 0
    assert len(_gerar(usuario, 11, 2026)) == 1
    assert len(_gerar(usuario, 1, 2027)) == 1
    assert len(_gerar(usuario, 2, 2027)) == 0


def test_so_os_fixos_da_pessoa(usuario, outro_usuario):
    _fixo(usuario, descricao="Da Ana")
    _fixo(outro_usuario, descricao="Da Bia")

    assert [g.descricao for g in _gerar(usuario, 12, 2026)] == ["Da Ana"]


def test_varios_fixos(usuario):
    _fixo(usuario, descricao="Aluguel", dia_vencimento=5)
    _fixo(usuario, descricao="Internet", dia_vencimento=10)

    assert [g.descricao for g in _gerar(usuario, 12, 2026)] == ["Aluguel", "Internet"]


def test_sem_fixos(usuario):
    assert _gerar(usuario, 12, 2026) == []
