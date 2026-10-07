"""Paleta de cores das categorias (FR-007; specs/006-categorias-gasto, research R-02).

A categoria guarda o código; o hex só vai para a interface, pela API. Assim um tom pode ser
ajustado (ex.: tema escuro, RNF-04) sem migrar dados. Fonte única da paleta: a interface não
decide quais cores existem (constituição, Princípio V).
"""

from collections import namedtuple

Cor = namedtuple("Cor", "codigo nome hex")

PALETA = (
    Cor("azul", "Azul", "#2563EB"),
    Cor("laranja", "Laranja", "#EA580C"),
    Cor("roxo", "Roxo", "#7C3AED"),
    Cor("vermelho", "Vermelho", "#DC2626"),
    Cor("rosa", "Rosa", "#DB2777"),
    Cor("ciano", "Ciano", "#0891B2"),
    Cor("cinza", "Cinza", "#6B7280"),
    Cor("verde", "Verde", "#16A34A"),
    Cor("amarelo", "Amarelo", "#CA8A04"),
    Cor("marrom", "Marrom", "#92400E"),
    Cor("oliva", "Oliva", "#65A30D"),
    Cor("indigo", "Índigo", "#4F46E5"),
)

CODIGOS = [cor.codigo for cor in PALETA]
CHOICES = [(cor.codigo, cor.nome) for cor in PALETA]

_POR_CODIGO = {cor.codigo: cor for cor in PALETA}


def obter_cor(codigo):
    """Devolve a ``Cor`` do código, ou ``None`` se o código não é da paleta."""
    return _POR_CODIGO.get(codigo)
