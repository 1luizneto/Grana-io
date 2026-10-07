"""Service de categorias (FR-001, FR-002; specs/006-categorias-gasto, research R-03)."""

import pytest

from gastos.models import Categoria
from gastos.services.categorias import criar_categorias_padrao

pytestmark = pytest.mark.django_db

PADRAO = {
    ("Moradia", "azul"),
    ("Alimentação", "laranja"),
    ("Transporte", "roxo"),
    ("Saúde", "vermelho"),
    ("Lazer", "rosa"),
    ("Educação", "ciano"),
    ("Outros", "cinza"),
}


def _da_conta(usuario):
    return set(Categoria.objects.do_dono(usuario).values_list("nome", "cor"))


def test_cria_as_7_categorias_padrao(usuario):
    criar_categorias_padrao(usuario)

    assert _da_conta(usuario) == PADRAO


def test_nao_duplica_quando_chamada_de_novo(usuario):
    criar_categorias_padrao(usuario)
    criar_categorias_padrao(usuario)

    assert Categoria.objects.do_dono(usuario).count() == 7


def test_nao_cria_para_quem_ja_tem_alguma_categoria(usuario):
    Categoria.objects.create(dono=usuario, nome="Pets", cor="verde")

    criar_categorias_padrao(usuario)

    assert _da_conta(usuario) == {("Pets", "verde")}


def test_nao_mexe_em_outra_conta(usuario, outro_usuario):
    Categoria.objects.create(dono=outro_usuario, nome="Pets", cor="verde")

    criar_categorias_padrao(usuario)

    assert _da_conta(outro_usuario) == {("Pets", "verde")}
