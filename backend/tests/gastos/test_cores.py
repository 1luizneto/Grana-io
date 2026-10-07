"""Paleta de cores das categorias (FR-007; specs/006-categorias-gasto, research R-02)."""

import re

from gastos.cores import CHOICES, CODIGOS, PALETA, obter_cor

ESPERADA = [
    ("azul", "Azul", "#2563EB"),
    ("laranja", "Laranja", "#EA580C"),
    ("roxo", "Roxo", "#7C3AED"),
    ("vermelho", "Vermelho", "#DC2626"),
    ("rosa", "Rosa", "#DB2777"),
    ("ciano", "Ciano", "#0891B2"),
    ("cinza", "Cinza", "#6B7280"),
    ("verde", "Verde", "#16A34A"),
    ("amarelo", "Amarelo", "#CA8A04"),
    ("marrom", "Marrom", "#92400E"),
    ("oliva", "Oliva", "#65A30D"),
    ("indigo", "Índigo", "#4F46E5"),
]


def test_paleta_tem_as_12_cores_na_ordem():
    assert [(c.codigo, c.nome, c.hex) for c in PALETA] == ESPERADA


def test_codigos_unicos_e_hex_valido():
    assert len(set(CODIGOS)) == 12
    assert all(re.fullmatch(r"#[0-9A-F]{6}", c.hex) for c in PALETA)


def test_codigos_e_choices_seguem_a_paleta():
    assert CODIGOS == [c for c, _, _ in ESPERADA]
    assert CHOICES == [(c, nome) for c, nome, _ in ESPERADA]


def test_obter_cor_pelo_codigo():
    assert obter_cor("verde").nome == "Verde"
    assert obter_cor("dourado") is None
