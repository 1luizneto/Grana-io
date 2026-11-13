"""Regra única de dinheiro do sistema (constituição, Princípio III; RNF-03).

Valores monetários são sempre ``Decimal`` (nunca ``float``), com 2 casas decimais e
arredondamento ``ROUND_HALF_UP`` (meio centavo vai para longe do zero).
"""

from decimal import ROUND_HALF_UP, Decimal

CENTAVO = Decimal("0.01")


def arredondar(valor):
    """Devolve ``valor`` como ``Decimal`` com exatamente 2 casas, pela regra ROUND_HALF_UP."""
    return Decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)
