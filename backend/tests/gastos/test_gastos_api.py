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


# Lista e totais (US2; FR-005, FR-006)


def _descricoes(resposta):
    return [g["descricao"] for g in resposta.json()]


def test_lista_do_mes_por_data_e_lancamento(usuario, cliente_autenticado):
    outubro = _mes(usuario)
    novembro = _mes(usuario, mes=11)
    _gasto(usuario, descricao="Uber", data=date(2026, 10, 5))
    _gasto(usuario, descricao="Feira", data=date(2026, 10, 2))
    _gasto(usuario, descricao="Mercado", data=date(2026, 10, 5))
    _gasto(usuario, descricao="Novembro", data=date(2026, 11, 1), mes=novembro)

    resposta = cliente_autenticado.get(URL, {"mes": outubro.pk})

    assert resposta.status_code == 200
    assert _descricoes(resposta) == ["Feira", "Uber", "Mercado"]


def test_lista_por_categoria(usuario, cliente_autenticado):
    transporte = _categoria(usuario, "Transporte", "roxo")
    _gasto(usuario, descricao="Mercado")
    _gasto(usuario, descricao="Uber", categoria=transporte)
    _gasto(usuario, descricao="Ônibus", categoria=transporte, mes=_mes(usuario, mes=11),
           data=date(2026, 11, 3))

    assert _descricoes(cliente_autenticado.get(URL, {"categoria": transporte.pk})) == [
        "Uber",
        "Ônibus",
    ]
    assert _descricoes(
        cliente_autenticado.get(URL, {"categoria": transporte.pk, "mes": _mes(usuario).pk})
    ) == ["Uber"]


@pytest.mark.parametrize(
    "filtro, mensagem",
    [("mes", "Informe o número do mês."), ("categoria", "Informe o número da categoria.")],
)
def test_filtro_que_nao_e_numero(cliente_autenticado, filtro, mensagem):
    resposta = cliente_autenticado.get(URL, {filtro: "abc"})

    assert resposta.status_code == 400
    assert resposta.json() == {filtro: [mensagem]}


def test_filtro_com_mes_de_outra_conta(usuario, outro_usuario, cliente_autenticado):
    _gasto(usuario)
    _gasto(outro_usuario)

    assert cliente_autenticado.get(URL, {"mes": _mes(outro_usuario).pk}).json() == []


def _totais(cliente, mes):
    return cliente.get(f"/api/meses/{mes.pk}/totais/")


def test_totais_do_mes(usuario, cliente_autenticado):
    alimentacao = _categoria(usuario)
    transporte = _categoria(usuario, "Transporte", "roxo")
    _gasto(usuario, valor="150.30")
    _gasto(usuario, valor="49.70")
    _gasto(usuario, valor="23.45", categoria=transporte)

    resposta = _totais(cliente_autenticado, _mes(usuario))

    assert resposta.status_code == 200
    assert resposta.json() == {
        "total": "223.45",
        "por_categoria": [
            {"categoria": alimentacao.pk, "nome": "Alimentação", "cor": "laranja",
             "total": "200.00", "quantidade": 2},
            {"categoria": transporte.pk, "nome": "Transporte", "cor": "roxo",
             "total": "23.45", "quantidade": 1},
        ],
    }


def test_totais_de_mes_sem_gastos(usuario, cliente_autenticado):
    assert _totais(cliente_autenticado, _mes(usuario)).json() == {
        "total": "0.00",
        "por_categoria": [],
    }


def test_totais_de_mes_de_outra_conta(outro_usuario, cliente_autenticado):
    resposta = _totais(cliente_autenticado, _mes(outro_usuario))

    assert resposta.status_code == 404
    assert resposta.json() == {"detail": "Não encontrado."}


def test_totais_acompanham_as_mudancas(usuario, cliente_autenticado):
    mes = _mes(usuario)
    cliente_autenticado.post(URL, _payload(usuario, valor="10.00"), format="json")
    assert _totais(cliente_autenticado, mes).json()["total"] == "10.00"

    gasto = Gasto.objects.get()
    cliente_autenticado.patch(_url(gasto), {"valor": "12.50"}, format="json")
    assert _totais(cliente_autenticado, mes).json()["total"] == "12.50"

    cliente_autenticado.delete(_url(gasto))
    assert _totais(cliente_autenticado, mes).json()["total"] == "0.00"


# Corrigir e excluir (US3; FR-007, FR-008)


@pytest.mark.parametrize(
    "mudanca, esperado",
    [
        ({"descricao": "Feira"}, {"descricao": "Feira"}),
        ({"valor": "12.50"}, {"valor": "12.50"}),
        ({"data": "2026-10-20"}, {"data": "2026-10-20"}),
        ({"forma_pagamento": "credito"}, {"forma_pagamento": "credito"}),
        ({"forma_pagamento": None}, {"forma_pagamento": ""}),
    ],
)
def test_alterar_cada_campo(usuario, cliente_autenticado, mudanca, esperado):
    gasto = _gasto(usuario, forma_pagamento="pix")

    resposta = cliente_autenticado.patch(_url(gasto), mudanca, format="json")

    assert resposta.status_code == 200
    assert resposta.json().items() >= esperado.items()


def test_alterar_categoria(usuario, cliente_autenticado):
    gasto = _gasto(usuario)
    transporte = _categoria(usuario, "Transporte", "roxo")

    resposta = cliente_autenticado.patch(_url(gasto), {"categoria": transporte.pk}, format="json")

    assert resposta.status_code == 200
    assert resposta.json()["categoria"] == transporte.pk


def test_put_completo(usuario, cliente_autenticado):
    gasto = _gasto(usuario)

    resposta = cliente_autenticado.put(
        _url(gasto), _payload(usuario, descricao="Feira", valor="9.90"), format="json"
    )

    assert resposta.status_code == 200
    assert resposta.json()["valor"] == "9.90"


@pytest.mark.parametrize(
    "mudanca, erro",
    [
        ({"valor": "0"}, {"valor": ["Informe um valor maior que zero."]}),
        ({"data": "2026-11-05"}, {"data": ["A data precisa estar dentro de 10/2026."]}),
        ({"descricao": ""}, {"descricao": OBRIGATORIO}),
    ],
)
def test_alterar_com_as_validacoes_do_lancamento(usuario, cliente_autenticado, mudanca, erro):
    gasto = _gasto(usuario)

    resposta = cliente_autenticado.patch(_url(gasto), mudanca, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == erro
    gasto.refresh_from_db()
    assert (gasto.descricao, gasto.valor, gasto.data) == ("Mercado", Decimal("150.30"), date(2026, 10, 5))


def test_mover_de_mes(usuario, cliente_autenticado):
    gasto = _gasto(usuario)
    novembro = _mes(usuario, mes=11)

    resposta = cliente_autenticado.patch(
        _url(gasto), {"mes": novembro.pk, "data": "2026-11-03"}, format="json"
    )

    assert resposta.status_code == 200
    assert resposta.json()["mes"] == novembro.pk


def test_mover_de_mes_sem_trocar_a_data(usuario, cliente_autenticado):
    gasto = _gasto(usuario)

    resposta = cliente_autenticado.patch(_url(gasto), {"mes": _mes(usuario, mes=11).pk}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"data": ["A data precisa estar dentro de 11/2026."]}


def test_mover_para_mes_de_outra_conta(usuario, outro_usuario, cliente_autenticado):
    gasto = _gasto(usuario)

    resposta = cliente_autenticado.patch(_url(gasto), {"mes": _mes(outro_usuario).pk}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"mes": NAO_ENCONTRADO}


def test_excluir(usuario, cliente_autenticado):
    gasto = _gasto(usuario)

    assert cliente_autenticado.delete(_url(gasto)).status_code == 204
    assert not Gasto.objects.exists()


@pytest.mark.parametrize("metodo", ["patch", "delete"])
def test_mes_fechado_bloqueia_alterar_e_excluir(usuario, cliente_autenticado, metodo):
    gasto = _gasto(usuario, mes=_mes(usuario, fechado=True))

    resposta = getattr(cliente_autenticado, metodo)(_url(gasto), {"valor": "1.00"}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == MES_FECHADO
    gasto.refresh_from_db()
    assert gasto.valor == Decimal("150.30")


def test_mover_para_mes_fechado(usuario, cliente_autenticado):
    gasto = _gasto(usuario)
    novembro = _mes(usuario, mes=11, fechado=True)

    resposta = cliente_autenticado.patch(
        _url(gasto), {"mes": novembro.pk, "data": "2026-11-03"}, format="json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {
        "detail": "O mês 11/2026 está fechado. Reabra o mês para alterar os gastos."
    }
    gasto.refresh_from_db()
    assert gasto.mes == _mes(usuario)


def test_tirar_de_mes_fechado(usuario, cliente_autenticado):
    gasto = _gasto(usuario, mes=_mes(usuario, fechado=True))
    novembro = _mes(usuario, mes=11)

    resposta = cliente_autenticado.patch(
        _url(gasto), {"mes": novembro.pk, "data": "2026-11-03"}, format="json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == MES_FECHADO
