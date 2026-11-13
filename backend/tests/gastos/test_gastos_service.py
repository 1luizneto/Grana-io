"""Regras de gastos que cruzam modelos (specs/008-lancar-gastos/research.md, R-03)."""

from datetime import date
from decimal import Decimal

import pytest

from gastos.models import Categoria, Gasto, MesReferencia
from gastos.services.gastos import (
    RegraViolada,
    excluir_categoria,
    exigir_mes_aberto,
    totais_do_mes,
    verificar_exclusao_do_mes,
)

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


# Totais (FR-006; research R-06)


def _categoria(dono, nome, cor="azul"):
    return Categoria.objects.get_or_create(dono=dono, nome=nome, defaults={"cor": cor})[0]


def _gasto(mes, categoria, valor, dia=5):
    return Gasto.objects.create(
        dono=mes.dono, mes=mes, categoria=categoria, descricao="Gasto", valor=Decimal(valor),
        data=date(mes.ano, mes.mes, dia),
    )


def test_soma_exata_de_centavos(usuario):
    mes = MesReferencia.objects.create(dono=usuario, mes=10, ano=2026)
    outros = _categoria(usuario, "Outros")
    _gasto(mes, outros, "0.10")
    _gasto(mes, outros, "0.20")

    assert totais_do_mes(mes).total == Decimal("0.30")


def test_totais_por_categoria(usuario):
    mes = MesReferencia.objects.create(dono=usuario, mes=10, ano=2026)
    alimentacao = _categoria(usuario, "Alimentação", "laranja")
    transporte = _categoria(usuario, "Transporte", "roxo")
    _gasto(mes, alimentacao, "150.30")
    _gasto(mes, alimentacao, "49.70")
    _gasto(mes, transporte, "23.45")

    totais = totais_do_mes(mes)

    assert totais.total == Decimal("223.45")
    assert [(t.categoria, t.nome, t.cor, t.total, t.quantidade) for t in totais.por_categoria] == [
        (alimentacao.pk, "Alimentação", "laranja", Decimal("200.00"), 2),
        (transporte.pk, "Transporte", "roxo", Decimal("23.45"), 1),
    ]


def test_empate_em_ordem_alfabetica(usuario):
    mes = MesReferencia.objects.create(dono=usuario, mes=10, ano=2026)
    _gasto(mes, _categoria(usuario, "Saúde"), "10.00")
    _gasto(mes, _categoria(usuario, "Água"), "10.00")

    assert [t.nome for t in totais_do_mes(mes).por_categoria] == ["Água", "Saúde"]


def test_so_os_gastos_do_mes(usuario, outro_usuario):
    outubro = MesReferencia.objects.create(dono=usuario, mes=10, ano=2026)
    novembro = MesReferencia.objects.create(dono=usuario, mes=11, ano=2026)
    da_bia = MesReferencia.objects.create(dono=outro_usuario, mes=10, ano=2026)
    _gasto(outubro, _categoria(usuario, "Outros"), "10.00")
    _gasto(novembro, _categoria(usuario, "Outros"), "99.00")
    _gasto(da_bia, _categoria(outro_usuario, "Outros"), "77.00")

    assert totais_do_mes(outubro).total == Decimal("10.00")


def test_mes_sem_gastos(usuario):
    totais = totais_do_mes(MesReferencia.objects.create(dono=usuario, mes=10, ano=2026))

    assert totais.total == Decimal("0.00")
    assert totais.total.as_tuple().exponent == -2
    assert totais.por_categoria == []


def test_totais_com_duas_casas(usuario):
    mes = MesReferencia.objects.create(dono=usuario, mes=10, ano=2026)
    _gasto(mes, _categoria(usuario, "Outros"), "10")

    totais = totais_do_mes(mes)

    assert str(totais.total) == "10.00"
    assert str(totais.por_categoria[0].total) == "10.00"


# Excluir mês e categoria sem perder gastos (FR-009, FR-010)

CATEGORIA_COM_GASTOS = "Esta categoria tem gastos. Escolha outra categoria para recebê-los."


def test_mes_aberto_e_vazio_pode_ser_excluido(usuario):
    verificar_exclusao_do_mes(MesReferencia.objects.create(dono=usuario, mes=10, ano=2026))


def test_mes_fechado_nao_pode_ser_excluido(usuario):
    mes = MesReferencia.objects.create(dono=usuario, mes=10, ano=2026, fechado=True)

    with pytest.raises(RegraViolada, match="^Reabra o mês antes de excluí-lo.$"):
        verificar_exclusao_do_mes(mes)


def test_mes_com_gastos_nao_pode_ser_excluido(usuario):
    mes = MesReferencia.objects.create(dono=usuario, mes=10, ano=2026)
    _gasto(mes, _categoria(usuario, "Outros"), "10.00")

    with pytest.raises(RegraViolada, match="^Exclua ou mova os gastos antes de excluir o mês.$"):
        verificar_exclusao_do_mes(mes)


def test_excluir_categoria_sem_gastos(usuario):
    lazer = _categoria(usuario, "Lazer")

    excluir_categoria(lazer, None)

    assert not Categoria.objects.filter(pk=lazer.pk).exists()


def test_categoria_com_gastos_exige_destino(usuario):
    mes = MesReferencia.objects.create(dono=usuario, mes=10, ano=2026)
    lazer = _categoria(usuario, "Lazer")
    gasto = _gasto(mes, lazer, "10.00")

    with pytest.raises(RegraViolada, match=f"^{CATEGORIA_COM_GASTOS}$"):
        excluir_categoria(lazer, None)

    gasto.refresh_from_db()
    assert gasto.categoria == lazer


def test_move_os_gastos_e_exclui(usuario):
    outubro = MesReferencia.objects.create(dono=usuario, mes=10, ano=2026)
    novembro = MesReferencia.objects.create(dono=usuario, mes=11, ano=2026, fechado=True)
    lazer = _categoria(usuario, "Lazer")
    outros = _categoria(usuario, "Outros")
    gastos = [_gasto(outubro, lazer, "10.00"), _gasto(novembro, lazer, "20.00")]

    excluir_categoria(lazer, outros)

    assert not Categoria.objects.filter(pk=lazer.pk).exists()
    for gasto in gastos:
        gasto.refresh_from_db()
        assert gasto.categoria == outros  # inclusive o do mês fechado (Clarifications)


def test_exclusao_da_categoria_e_tudo_ou_nada(usuario, monkeypatch):
    mes = MesReferencia.objects.create(dono=usuario, mes=10, ano=2026)
    lazer = _categoria(usuario, "Lazer")
    outros = _categoria(usuario, "Outros")
    gasto = _gasto(mes, lazer, "10.00")

    def falhar(self, *args, **kwargs):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(Categoria, "delete", falhar)

    with pytest.raises(RuntimeError):
        excluir_categoria(lazer, outros)

    gasto.refresh_from_db()
    assert gasto.categoria == lazer
