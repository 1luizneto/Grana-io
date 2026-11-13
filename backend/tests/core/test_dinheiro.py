"""Regra única de arredondamento de dinheiro (constituição, Princípio III; RNF-03)."""

from decimal import Decimal

from core.dinheiro import CENTAVO, arredondar


def test_centavo():
    assert CENTAVO == Decimal("0.01")


def test_arredonda_meio_centavo_para_cima():
    assert arredondar(Decimal("2.345")) == Decimal("2.35")
    assert arredondar(Decimal("2.344")) == Decimal("2.34")


def test_negativos_arredondam_para_longe_do_zero():
    assert arredondar(Decimal("-2.345")) == Decimal("-2.35")


def test_sempre_duas_casas():
    resultado = arredondar(Decimal("5"))

    assert resultado == Decimal("5.00")
    assert resultado.as_tuple().exponent == -2


def test_aceita_inteiro():
    assert arredondar(0) == Decimal("0.00")
