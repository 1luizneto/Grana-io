"""API de categorias (specs/006-categorias-gasto/contracts/api-categorias.md)."""

import pytest

from gastos.models import Categoria
from gastos.serializers import CategoriaSerializer
from tests.isolamento import CasosDeIsolamento

pytestmark = pytest.mark.django_db

URL = "/api/categorias/"
NOME_REPETIDO = {"nome": ["Já existe uma categoria com este nome."]}


def _categoria(dono, nome, cor="azul"):
    return Categoria.objects.create(dono=dono, nome=nome, cor=cor)


class TestIsolamentoCategoria(CasosDeIsolamento):
    modelo = Categoria
    url_lista = URL
    payload_criacao = {"nome": "Pets", "cor": "verde"}
    payload_alteracao = {"nome": "Bichos"}

    def criar(self, usuario):
        # Nome único por conta: cada chamada gera um nome novo.
        return _categoria(usuario, f"Categoria {Categoria.objects.count() + 1}")


# Listar e abrir (FR-003)


def test_lista_em_ordem_alfabetica_com_os_campos_do_contrato(usuario, cliente_autenticado):
    for nome in ["transporte", "Água", "Banco"]:
        _categoria(usuario, nome)

    resposta = cliente_autenticado.get(URL)

    assert resposta.status_code == 200
    assert [c["nome"] for c in resposta.json()] == ["Água", "Banco", "transporte"]
    assert set(resposta.json()[0]) == {"id", "nome", "cor"}


# Criar (FR-004, FR-005)


def test_cria_sem_os_espacos_das_pontas(usuario, cliente_autenticado):
    resposta = cliente_autenticado.post(URL, {"nome": "  Pets  ", "cor": "verde"}, format="json")

    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "Pets"
    assert Categoria.objects.get(pk=resposta.json()["id"]).dono == usuario


@pytest.mark.parametrize("repetido", ["Pets", "pets", "PETS", " pets "])
def test_nome_repetido_na_conta_e_recusado(usuario, cliente_autenticado, repetido):
    _categoria(usuario, "Pets")

    resposta = cliente_autenticado.post(URL, {"nome": repetido, "cor": "verde"}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == NOME_REPETIDO
    assert Categoria.objects.do_dono(usuario).count() == 1


def test_mesmo_nome_em_outra_conta_e_aceito(usuario, outro_usuario, cliente_da_bia):
    _categoria(usuario, "Pets")

    resposta = cliente_da_bia.post(URL, {"nome": "Pets", "cor": "verde"}, format="json")

    assert resposta.status_code == 201


@pytest.mark.parametrize("vazio", ["", "   "])
def test_nome_vazio_e_obrigatorio(cliente_autenticado, vazio):
    resposta = cliente_autenticado.post(URL, {"nome": vazio, "cor": "verde"}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"nome": ["Este campo é obrigatório."]}


def test_nome_com_mais_de_50_caracteres_e_recusado(cliente_autenticado):
    resposta = cliente_autenticado.post(URL, {"nome": "a" * 51, "cor": "verde"}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {
        "nome": ["Certifique-se de que este campo não tenha mais de 50 caracteres."]
    }


# Renomear (FR-006)


def test_renomeia_e_mantem_a_cor(usuario, cliente_autenticado):
    lazer = _categoria(usuario, "Lazer", cor="rosa")

    resposta = cliente_autenticado.patch(f"{URL}{lazer.pk}/", {"nome": "Lazer e viagens"}, format="json")

    assert resposta.status_code == 200
    assert resposta.json() == {"id": lazer.pk, "nome": "Lazer e viagens", "cor": "rosa"}


def test_renomear_para_o_proprio_nome_com_outra_grafia(usuario, cliente_autenticado):
    lazer = _categoria(usuario, "lazer")

    resposta = cliente_autenticado.patch(f"{URL}{lazer.pk}/", {"nome": "Lazer"}, format="json")

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Lazer"


def test_renomear_para_nome_de_outra_categoria_e_recusado(usuario, cliente_autenticado):
    _categoria(usuario, "Saúde")
    lazer = _categoria(usuario, "Lazer")

    resposta = cliente_autenticado.patch(f"{URL}{lazer.pk}/", {"nome": "SAÚDE"}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == NOME_REPETIDO
    lazer.refresh_from_db()
    assert lazer.nome == "Lazer"


# Corrida (research R-06)


def test_corrida_vira_erro_no_campo_e_nao_erro_500(usuario, cliente_autenticado, monkeypatch):
    # Simula dois envios simultâneos: a checagem do serializer não vê o outro, só o banco segura.
    monkeypatch.setattr(CategoriaSerializer, "validate_nome", lambda self, valor: valor)
    _categoria(usuario, "Pets")

    resposta = cliente_autenticado.post(URL, {"nome": "pets", "cor": "verde"}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == NOME_REPETIDO
    assert Categoria.objects.do_dono(usuario).count() == 1
