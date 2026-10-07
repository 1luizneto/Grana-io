"""Model Categoria (FR-003, FR-005; specs/006-categorias-gasto/data-model.md)."""

import pytest
from django.db import IntegrityError, transaction

from core.models import OwnedModel
from gastos.cores import CHOICES
from gastos.models import Categoria

pytestmark = pytest.mark.django_db


def _categoria(dono, nome, cor="azul"):
    return Categoria.objects.create(dono=dono, nome=nome, cor=cor)


def test_categoria_tem_dono():
    assert issubclass(Categoria, OwnedModel)


def test_campos():
    nome = Categoria._meta.get_field("nome")
    cor = Categoria._meta.get_field("cor")

    assert nome.max_length == 50
    assert cor.max_length == 20
    assert list(cor.choices) == CHOICES


def test_nome_repetido_na_mesma_conta_sem_diferenciar_maiusculas(usuario):
    _categoria(usuario, "Pets")

    with pytest.raises(IntegrityError, match="gastos_categoria_nome_por_dono"), transaction.atomic():
        _categoria(usuario, "pets")

    assert Categoria.objects.count() == 1


def test_mesmo_nome_em_contas_diferentes(usuario, outro_usuario):
    _categoria(usuario, "Pets")
    _categoria(outro_usuario, "Pets")

    assert Categoria.objects.count() == 2


def test_acento_conta_na_unicidade(usuario):
    _categoria(usuario, "Saude")
    _categoria(usuario, "Saúde")

    assert Categoria.objects.do_dono(usuario).count() == 2


def test_ordem_alfabetica_sem_diferenciar_maiusculas_e_com_acentos(usuario):
    # A collation padrão do banco ordena "Água" e "Ônibus" depois de "zebra" (research R-10).
    for nome in ["zebra", "Ônibus", "Banco", "Água", "academia"]:
        _categoria(usuario, nome)

    nomes = [c.nome for c in Categoria.objects.do_dono(usuario)]

    assert nomes == ["academia", "Água", "Banco", "Ônibus", "zebra"]
