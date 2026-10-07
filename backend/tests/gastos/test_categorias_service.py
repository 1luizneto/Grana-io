"""Service de categorias (FR-001, FR-002; specs/006-categorias-gasto, research R-03)."""

import pytest

from gastos.cores import PALETA
from gastos.models import Categoria
from gastos.services.categorias import criar_categorias_padrao, escolher_cor_livre

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


# Cor automática (FR-007; research R-07)


def test_cor_livre_e_a_primeira_da_paleta_que_a_pessoa_nao_usa(usuario):
    Categoria.objects.create(dono=usuario, nome="A", cor="azul")
    Categoria.objects.create(dono=usuario, nome="B", cor="laranja")

    assert escolher_cor_livre(usuario) == "roxo"


def test_sem_categorias_a_cor_livre_e_a_primeira(usuario):
    assert escolher_cor_livre(usuario) == "azul"


def test_com_todas_as_cores_em_uso_segue_a_ordem_da_paleta(usuario):
    for posicao, cor in enumerate(PALETA):
        Categoria.objects.create(dono=usuario, nome=f"C{posicao}", cor=cor.codigo)
    Categoria.objects.create(dono=usuario, nome="Extra", cor="azul")

    # 13 categorias: posição 13 % 12 = 1.
    assert escolher_cor_livre(usuario) == PALETA[1].codigo


def test_cores_de_outra_conta_nao_contam(usuario, outro_usuario):
    Categoria.objects.create(dono=outro_usuario, nome="Pets", cor="azul")

    assert escolher_cor_livre(usuario) == "azul"
