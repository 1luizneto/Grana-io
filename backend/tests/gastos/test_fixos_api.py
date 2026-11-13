"""API de gastos fixos (specs/010-gastos-fixos/contracts/api-fixos.md)."""

from datetime import date
from decimal import Decimal

import pytest

from gastos.models import Categoria, GastoFixo
from tests.isolamento import CasosDeIsolamento

pytestmark = pytest.mark.django_db

URL = "/api/fixos/"
OBRIGATORIO = ["Este campo é obrigatório."]


def _categoria(dono, nome="Moradia", cor="azul"):
    return Categoria.objects.get_or_create(dono=dono, nome=nome, defaults={"cor": cor})[0]


def _fixo(dono, **mudancas):
    dados = {
        "descricao": "Aluguel",
        "valor": Decimal("1500.00"),
        "categoria": _categoria(dono),
        "dia_vencimento": 5,
        "inicio": date(2026, 11, 1),
        **mudancas,
    }
    return GastoFixo.objects.create(dono=dono, **dados)


def _payload(dono, **mudancas):
    return {
        "descricao": "Aluguel",
        "valor": "1500.00",
        "categoria": _categoria(dono).pk,
        "forma_pagamento": "pix",
        "dia_vencimento": 5,
        "inicio": "2026-11",
        **mudancas,
    }


def _url(fixo):
    return f"{URL}{fixo.pk}/"


class TestIsolamentoFixo(CasosDeIsolamento):
    modelo = GastoFixo
    url_lista = URL
    payload_alteracao = {"valor": "1600.00"}

    def criar(self, usuario):
        return _fixo(usuario)

    def montar_payload_criacao(self, usuario):
        return _payload(usuario)


def test_cadastrar(usuario, cliente_autenticado):
    payload = _payload(usuario)

    resposta = cliente_autenticado.post(URL, payload, format="json")

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo == {
        "id": corpo["id"],
        "descricao": "Aluguel",
        "valor": "1500.00",
        "categoria": payload["categoria"],
        "forma_pagamento": "pix",
        "dia_vencimento": 5,
        "inicio": "2026-11",
        "fim": None,
        "ativo": True,
    }
    assert GastoFixo.objects.get().inicio == date(2026, 11, 1)


def test_cadastrar_com_fim(usuario, cliente_autenticado):
    resposta = cliente_autenticado.post(URL, _payload(usuario, fim="2027-01"), format="json")

    assert resposta.status_code == 201
    assert resposta.json()["fim"] == "2027-01"
    assert GastoFixo.objects.get().fim == date(2027, 1, 1)


def test_fim_igual_ao_inicio(usuario, cliente_autenticado):
    resposta = cliente_autenticado.post(URL, _payload(usuario, fim="2026-11"), format="json")

    assert resposta.status_code == 201


def test_fim_antes_do_inicio(usuario, cliente_autenticado):
    resposta = cliente_autenticado.post(URL, _payload(usuario, fim="2026-10"), format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {
        "fim": ["O mês de fim precisa ser igual ou posterior ao de início."]
    }


def test_fim_antes_do_inicio_na_alteracao(usuario, cliente_autenticado):
    fixo = _fixo(usuario)

    resposta = cliente_autenticado.patch(_url(fixo), {"fim": "2026-01"}, format="json")

    assert resposta.status_code == 400
    assert "fim" in resposta.json()


@pytest.mark.parametrize("dia", [0, 32, "x", None])
def test_dia_invalido(usuario, cliente_autenticado, dia):
    resposta = cliente_autenticado.post(URL, _payload(usuario, dia_vencimento=dia), format="json")

    assert resposta.status_code == 400
    esperado = OBRIGATORIO if dia is None else ["Informe um dia de 1 a 31."]
    assert resposta.json() == {"dia_vencimento": esperado}


@pytest.mark.parametrize(
    "inicio, mensagem",
    [
        ("11/2026", "Informe o mês no formato AAAA-MM."),
        ("2026-13", "Informe o mês no formato AAAA-MM."),
        ("2026-11-05", "Informe o mês no formato AAAA-MM."),
        ("1999-12", "Informe um ano de 2000 a 2100."),
        ("", "Este campo é obrigatório."),
    ],
)
def test_inicio_invalido(usuario, cliente_autenticado, inicio, mensagem):
    resposta = cliente_autenticado.post(URL, _payload(usuario, inicio=inicio), format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"inicio": [mensagem]}


def test_validacoes_do_gasto(usuario, outro_usuario, cliente_autenticado):
    payload = _payload(
        usuario, descricao="", valor="0", categoria=_categoria(outro_usuario).pk
    )

    resposta = cliente_autenticado.post(URL, payload, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {
        "descricao": OBRIGATORIO,
        "valor": ["Informe um valor maior que zero."],
        "categoria": ["Registro não encontrado."],
    }


def test_lista_por_dia_de_vencimento(usuario, cliente_autenticado):
    _fixo(usuario, descricao="Internet", dia_vencimento=10)
    _fixo(usuario, descricao="Aluguel", dia_vencimento=5)

    resposta = cliente_autenticado.get(URL)

    assert [f["descricao"] for f in resposta.json()] == ["Aluguel", "Internet"]


def test_desativar_e_reativar(usuario, cliente_autenticado):
    fixo = _fixo(usuario)

    desativado = cliente_autenticado.patch(_url(fixo), {"ativo": False}, format="json")
    reativado = cliente_autenticado.patch(_url(fixo), {"ativo": True}, format="json")

    assert desativado.json()["ativo"] is False
    assert reativado.json()["ativo"] is True


def test_sem_sessao(cliente):
    assert cliente.get(URL).status_code == 401
