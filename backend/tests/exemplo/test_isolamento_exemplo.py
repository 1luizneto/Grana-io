"""Isolamento por dono provado com os registros de exemplo (spec 004; quickstart S2)."""

from decimal import Decimal

import pytest

from tests.exemplo.models import ItemExemplo
from tests.isolamento import CasosDeIsolamento

pytestmark = [pytest.mark.django_db, pytest.mark.urls("tests.exemplo.urls")]

URL_ITENS = "/api/exemplo/itens/"


def _item(dono, descricao="Mercado", valor="10.00"):
    return ItemExemplo.objects.create(dono=dono, descricao=descricao, valor=Decimal(valor))


class TestIsolamentoItemExemplo(CasosDeIsolamento):
    url_lista = URL_ITENS
    payload_criacao = {"descricao": "Padaria", "valor": "12.50"}
    payload_alteracao = {"descricao": "Padaria do bairro"}

    def criar(self, usuario):
        return _item(usuario)


def test_busca_so_do_dono(usuario, outro_usuario, cliente_autenticado):
    do_ana = _item(usuario, descricao="Mercado do centro")
    _item(usuario, descricao="Farmácia")
    _item(outro_usuario, descricao="Mercado da Bia")

    resposta = cliente_autenticado.get(URL_ITENS, {"busca": "mercado"})

    assert resposta.status_code == 200
    assert [item["id"] for item in resposta.json()] == [do_ana.pk]


def test_total_so_do_dono(usuario, outro_usuario, cliente_autenticado):
    _item(usuario, valor="10.00")
    _item(usuario, valor="20.00")
    _item(outro_usuario, valor="99.00")

    resposta = cliente_autenticado.get(f"{URL_ITENS}total/")

    assert resposta.status_code == 200
    assert resposta.json() == {"quantidade": 2, "soma": "30.00"}


def test_id_mal_formado_e_nao_encontrado(usuario, cliente_autenticado):
    item = _item(usuario)

    mal_formado = cliente_autenticado.get(f"{URL_ITENS}abc/")
    inexistente = cliente_autenticado.get(f"{URL_ITENS}{item.pk + 1000}/")

    assert mal_formado.status_code == inexistente.status_code == 404
    assert mal_formado.json() == inexistente.json()


def test_texto_do_nao_encontrado(cliente_autenticado):
    resposta = cliente_autenticado.get(f"{URL_ITENS}999999/")

    assert resposta.json() == {"detail": "Não encontrado."}


def test_sem_sessao_e_recusado(usuario, cliente):
    _item(usuario)

    resposta = cliente.get(URL_ITENS)

    assert resposta.status_code == 401
    assert "Mercado" not in resposta.content.decode()
