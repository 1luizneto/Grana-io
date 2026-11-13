"""API de gastos fixos (specs/010-gastos-fixos/contracts/api-fixos.md)."""

from datetime import date
from decimal import Decimal

import pytest

from gastos.models import Categoria, Gasto, GastoFixo
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


# Alterar, encerrar, desativar e excluir (US3; FR-005, FR-006)


def _criar_mes(cliente, mes, ano):
    return cliente.post("/api/meses/", {"mes": mes, "ano": ano}, format="json").json()["id"]


def _valores_do_mes(cliente, mes_id):
    return [g["valor"] for g in cliente.get("/api/gastos/", {"mes": mes_id}).json()]


def test_mudar_o_valor_so_vale_para_os_meses_seguintes(usuario, cliente_autenticado):
    fixo = _fixo(usuario)
    dezembro = _criar_mes(cliente_autenticado, 12, 2026)

    cliente_autenticado.patch(_url(fixo), {"valor": "1600.00"}, format="json")
    janeiro = _criar_mes(cliente_autenticado, 1, 2027)

    assert _valores_do_mes(cliente_autenticado, dezembro) == ["1500.00"]
    assert _valores_do_mes(cliente_autenticado, janeiro) == ["1600.00"]


def test_desativado_nao_entra_nos_meses_seguintes(usuario, cliente_autenticado):
    fixo = _fixo(usuario)
    cliente_autenticado.patch(_url(fixo), {"ativo": False}, format="json")

    assert _valores_do_mes(cliente_autenticado, _criar_mes(cliente_autenticado, 12, 2026)) == []

    cliente_autenticado.patch(_url(fixo), {"ativo": True}, format="json")

    assert _valores_do_mes(cliente_autenticado, _criar_mes(cliente_autenticado, 1, 2027)) == [
        "1500.00"
    ]


def test_fim_encerra(usuario, cliente_autenticado):
    fixo = _fixo(usuario)
    cliente_autenticado.patch(_url(fixo), {"fim": "2026-12"}, format="json")

    dezembro = _criar_mes(cliente_autenticado, 12, 2026)

    assert len(_valores_do_mes(cliente_autenticado, dezembro)) == 1
    assert _valores_do_mes(cliente_autenticado, _criar_mes(cliente_autenticado, 1, 2027)) == []


def test_excluir_mantem_os_gastos_gerados(usuario, cliente_autenticado):
    fixo = _fixo(usuario)
    dezembro = _criar_mes(cliente_autenticado, 12, 2026)

    resposta = cliente_autenticado.delete(_url(fixo))

    assert resposta.status_code == 204
    [gasto] = cliente_autenticado.get("/api/gastos/", {"mes": dezembro}).json()
    assert gasto["descricao"] == "Aluguel"
    assert gasto["fixo"] is None
    assert Gasto.objects.count() == 1


def test_categoria_so_com_fixos_exige_destino(usuario, cliente_autenticado):
    fixo = _fixo(usuario)
    outros = _categoria(usuario, "Outros", "cinza")

    sem_destino = cliente_autenticado.delete(f"/api/categorias/{fixo.categoria_id}/")
    com_destino = cliente_autenticado.delete(
        f"/api/categorias/{fixo.categoria_id}/?mover_para={outros.pk}"
    )

    assert sem_destino.status_code == 400
    assert sem_destino.json() == {
        "detail": "Esta categoria tem gastos. Escolha outra categoria para recebê-los."
    }
    assert com_destino.status_code == 204
    fixo.refresh_from_db()
    assert fixo.categoria == outros
