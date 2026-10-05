"""Isolamento por dono provado com os registros de exemplo (spec 004; quickstart S2)."""

from decimal import Decimal

import pytest

from tests.exemplo.models import GrupoExemplo, ItemExemplo
from tests.isolamento import CasosDeIsolamento

pytestmark = [pytest.mark.django_db, pytest.mark.urls("tests.exemplo.urls")]

URL_ITENS = "/api/exemplo/itens/"
URL_GRUPOS = "/api/exemplo/grupos/"


def _item(dono, descricao="Mercado", valor="10.00"):
    return ItemExemplo.objects.create(dono=dono, descricao=descricao, valor=Decimal(valor))


class TestIsolamentoItemExemplo(CasosDeIsolamento):
    modelo = ItemExemplo
    url_lista = URL_ITENS
    payload_criacao = {"descricao": "Padaria", "valor": "12.50"}
    payload_alteracao = {"descricao": "Padaria do bairro"}

    def criar(self, usuario):
        return _item(usuario)


class TestIsolamentoGrupoExemplo(CasosDeIsolamento):
    modelo = GrupoExemplo
    url_lista = URL_GRUPOS
    payload_criacao = {"nome": "Lazer"}
    payload_alteracao = {"nome": "Lazer e viagens"}

    def criar(self, usuario):
        # Nome único por dono: cada chamada gera um nome novo.
        return GrupoExemplo.objects.create(
            dono=usuario, nome=f"Grupo {GrupoExemplo.objects.count() + 1}"
        )


def test_item_com_grupo_de_outra_conta_e_recusado(outro_usuario, cliente_autenticado):
    da_bia = GrupoExemplo.objects.create(dono=outro_usuario, nome="Casa")
    payload = {"descricao": "Luz", "valor": "80.00"}

    de_outra_conta = cliente_autenticado.post(URL_ITENS, {**payload, "grupo": da_bia.pk}, format="json")
    inexistente = cliente_autenticado.post(
        URL_ITENS, {**payload, "grupo": da_bia.pk + 1000}, format="json"
    )

    assert de_outra_conta.status_code == inexistente.status_code == 400
    assert de_outra_conta.json() == inexistente.json() == {"grupo": ["Registro não encontrado."]}
    assert not ItemExemplo.objects.exists()


def test_nome_de_grupo_repetido_entre_contas_e_aceito(cliente_autenticado, cliente_da_bia):
    assert cliente_autenticado.post(URL_GRUPOS, {"nome": "Mercado"}, format="json").status_code == 201
    assert cliente_da_bia.post(URL_GRUPOS, {"nome": "Mercado"}, format="json").status_code == 201


def test_nome_de_grupo_repetido_na_mesma_conta_e_recusado(cliente_autenticado):
    cliente_autenticado.post(URL_GRUPOS, {"nome": "Mercado"}, format="json")

    resposta = cliente_autenticado.post(URL_GRUPOS, {"nome": "Mercado"}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"non_field_errors": ["Já existe um grupo com este nome."]}
    assert "dono" not in resposta.content.decode()


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
