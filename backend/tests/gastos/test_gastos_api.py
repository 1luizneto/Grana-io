"""API de gastos (specs/008-lancar-gastos/contracts/api-gastos.md)."""

from datetime import date
from decimal import Decimal

import pytest

from gastos.models import Categoria, Gasto, MesReferencia
from tests.isolamento import CasosDeIsolamento

pytestmark = pytest.mark.django_db

URL = "/api/gastos/"
OBRIGATORIO = ["Este campo é obrigatório."]
NAO_ENCONTRADO = ["Registro não encontrado."]
MES_FECHADO = {"detail": "O mês 10/2026 está fechado. Reabra o mês para alterar os gastos."}


def _mes(dono, mes=10, ano=2026, **extra):
    return MesReferencia.objects.get_or_create(dono=dono, mes=mes, ano=ano, defaults=extra)[0]


def _categoria(dono, nome="Alimentação", cor="laranja"):
    return Categoria.objects.get_or_create(dono=dono, nome=nome, defaults={"cor": cor})[0]


def _gasto(
    dono, descricao="Mercado", valor="150.30", data=date(2026, 10, 5), mes=None, categoria=None,
    **extra,
):
    return Gasto.objects.create(
        dono=dono,
        descricao=descricao,
        valor=Decimal(valor),
        data=data,
        mes=mes or _mes(dono),
        categoria=categoria or _categoria(dono),
        **extra,
    )


def _payload(dono, **mudancas):
    return {
        "descricao": "Mercado",
        "valor": "150.30",
        "data": "2026-10-05",
        "mes": _mes(dono).pk,
        "categoria": _categoria(dono).pk,
        "forma_pagamento": "pix",
        **mudancas,
    }


def _url(gasto):
    return f"{URL}{gasto.pk}/"


class TestIsolamentoGasto(CasosDeIsolamento):
    modelo = Gasto
    url_lista = URL
    payload_alteracao = {"descricao": "Feira"}

    def criar(self, usuario):
        return _gasto(usuario)

    def montar_payload_criacao(self, usuario):
        # Mês e categoria precisam ser da própria Ana.
        return _payload(usuario)


# Lançar (US1; FR-001 a FR-004, FR-008)


def test_lancar(usuario, cliente_autenticado):
    payload = _payload(usuario)

    resposta = cliente_autenticado.post(URL, payload, format="json")

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo == {
        "id": corpo["id"],
        "descricao": "Mercado",
        "valor": "150.30",
        "data": "2026-10-05",
        "forma_pagamento": "pix",
        "mes": payload["mes"],
        "categoria": payload["categoria"],
    }
    assert Gasto.objects.get().dono == usuario


def test_valor_numerico_sai_com_duas_casas(usuario, cliente_autenticado):
    resposta = cliente_autenticado.post(URL, _payload(usuario, valor=150.3), format="json")

    assert resposta.status_code == 201
    assert resposta.json()["valor"] == "150.30"


@pytest.mark.parametrize("forma", ["ausente", "", None])
def test_forma_de_pagamento_opcional(usuario, cliente_autenticado, forma):
    payload = _payload(usuario, forma_pagamento=forma)
    if forma == "ausente":
        del payload["forma_pagamento"]

    resposta = cliente_autenticado.post(URL, payload, format="json")

    assert resposta.status_code == 201
    assert resposta.json()["forma_pagamento"] == ""


def test_forma_de_pagamento_desconhecida(usuario, cliente_autenticado):
    resposta = cliente_autenticado.post(
        URL, _payload(usuario, forma_pagamento="cheque"), format="json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {
        "forma_pagamento": ["Escolha uma forma de pagamento: dinheiro, débito, crédito ou Pix."]
    }


def test_descricao_aparada(usuario, cliente_autenticado):
    resposta = cliente_autenticado.post(URL, _payload(usuario, descricao="  Feira  "), format="json")

    assert resposta.json()["descricao"] == "Feira"


@pytest.mark.parametrize("descricao", ["", "   ", None])
def test_descricao_obrigatoria(usuario, cliente_autenticado, descricao):
    resposta = cliente_autenticado.post(URL, _payload(usuario, descricao=descricao), format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"descricao": OBRIGATORIO}


def test_descricao_longa(usuario, cliente_autenticado):
    resposta = cliente_autenticado.post(URL, _payload(usuario, descricao="x" * 101), format="json")

    assert resposta.json() == {
        "descricao": ["Certifique-se de que este campo não tenha mais de 100 caracteres."]
    }


@pytest.mark.parametrize(
    "valor, mensagem",
    [
        ("abc", "Informe um valor numérico, como 12.50."),
        ("12,50", "Informe um valor numérico, como 12.50."),
        ("NaN", "Informe um valor numérico, como 12.50."),
        ("0", "Informe um valor maior que zero."),
        ("0.00", "Informe um valor maior que zero."),
        (-5, "Informe um valor maior que zero."),
        ("10.555", "Use no máximo 2 casas decimais."),
        ("10000000000.00", "Informe um valor de até 9999999999.99."),
        ("", "Este campo é obrigatório."),
        (None, "Este campo é obrigatório."),
    ],
)
def test_valor_invalido(usuario, cliente_autenticado, valor, mensagem):
    resposta = cliente_autenticado.post(URL, _payload(usuario, valor=valor), format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"valor": [mensagem]}
    assert not Gasto.objects.exists()


def test_valor_no_limite(usuario, cliente_autenticado):
    resposta = cliente_autenticado.post(URL, _payload(usuario, valor="9999999999.99"), format="json")

    assert resposta.status_code == 201


def test_valor_ausente(usuario, cliente_autenticado):
    payload = _payload(usuario)
    del payload["valor"]

    assert cliente_autenticado.post(URL, payload, format="json").json() == {"valor": OBRIGATORIO}


@pytest.mark.parametrize("data", ["2026-13-01", "2026-09-31", "ontem"])
def test_data_invalida(usuario, cliente_autenticado, data):
    resposta = cliente_autenticado.post(URL, _payload(usuario, data=data), format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"data": ["Informe uma data válida no formato AAAA-MM-DD."]}


@pytest.mark.parametrize("data", ["2026-11-05", "2026-09-30", "2025-10-05"])
def test_data_fora_do_mes(usuario, cliente_autenticado, data):
    resposta = cliente_autenticado.post(URL, _payload(usuario, data=data), format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"data": ["A data precisa estar dentro de 10/2026."]}


@pytest.mark.parametrize("data", ["2026-10-01", "2026-10-31"])
def test_limites_do_mes(usuario, cliente_autenticado, data):
    resposta = cliente_autenticado.post(URL, _payload(usuario, data=data), format="json")

    assert resposta.status_code == 201


def test_campos_obrigatorios(cliente_autenticado):
    resposta = cliente_autenticado.post(URL, {}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {
        campo: OBRIGATORIO for campo in ["descricao", "valor", "data", "mes", "categoria"]
    }


def test_mes_e_categoria_de_outra_conta(usuario, outro_usuario, cliente_autenticado):
    payload = _payload(usuario, mes=_mes(outro_usuario).pk, categoria=_categoria(outro_usuario).pk)

    resposta = cliente_autenticado.post(URL, payload, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"mes": NAO_ENCONTRADO, "categoria": NAO_ENCONTRADO}


def test_mes_fechado_nao_aceita_gasto(usuario, cliente_autenticado):
    _mes(usuario, fechado=True)

    resposta = cliente_autenticado.post(URL, _payload(usuario), format="json")

    assert resposta.status_code == 400
    assert resposta.json() == MES_FECHADO
    assert not Gasto.objects.exists()


def test_lancar_sem_sessao(cliente):
    assert cliente.post(URL, {}, format="json").status_code == 401


# Formas de pagamento (R-08)


def test_formas_de_pagamento(cliente_autenticado):
    resposta = cliente_autenticado.get(f"{URL}formas-pagamento/")

    assert resposta.status_code == 200
    assert resposta.json() == [
        {"codigo": "dinheiro", "nome": "Dinheiro"},
        {"codigo": "debito", "nome": "Débito"},
        {"codigo": "credito", "nome": "Crédito"},
        {"codigo": "pix", "nome": "Pix"},
    ]


def test_formas_de_pagamento_sem_sessao(cliente):
    assert cliente.get(f"{URL}formas-pagamento/").status_code == 401
