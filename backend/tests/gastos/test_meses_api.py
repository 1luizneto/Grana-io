"""API de meses de referência (specs/007-mes-referencia/contracts/api-meses.md)."""

import pytest

from gastos.models import MesReferencia
from gastos.serializers import MesReferenciaSerializer
from tests.isolamento import CasosDeIsolamento

pytestmark = pytest.mark.django_db

URL = "/api/meses/"
MES_REPETIDO = {"non_field_errors": ["Este mês já foi criado."]}
MES_INVALIDO = ["Informe um mês de 1 a 12."]
ANO_INVALIDO = ["Informe um ano de 2000 a 2100."]
OBRIGATORIO = ["Este campo é obrigatório."]


def _mes(dono, mes=10, ano=2026, **extra):
    return MesReferencia.objects.create(dono=dono, mes=mes, ano=ano, **extra)


class TestIsolamentoMes(CasosDeIsolamento):
    modelo = MesReferencia
    url_lista = URL
    payload_criacao = {"mes": 10, "ano": 2026}
    # Os meses do kit nascem fechados e a alteração os reabre: assim o kit pode excluir o mês
    # do dono depois do PATCH (mês fechado não se exclui), e "alterar de outra conta não muda
    # nada" confere que o mês da Bia continua fechado.
    payload_alteracao = {"fechado": False}

    def criar(self, usuario):
        # Mês único por conta: cada chamada gera um mês novo.
        n = MesReferencia.objects.count()
        return _mes(usuario, mes=n % 12 + 1, ano=2026 + n // 12, fechado=True)


# Criar (US1; FR-001, FR-002, FR-009)


def test_criar(cliente_autenticado):
    resposta = cliente_autenticado.post(URL, {"mes": 10, "ano": 2026}, format="json")

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo == {"id": corpo["id"], "mes": 10, "ano": 2026, "rotulo": "10/2026", "fechado": False}


def test_criar_com_numeros_em_texto(cliente_autenticado):
    resposta = cliente_autenticado.post(URL, {"mes": "3", "ano": "2027"}, format="json")

    assert resposta.status_code == 201
    assert resposta.json()["rotulo"] == "03/2027"


def test_mes_nasce_aberto_mesmo_pedindo_fechado(cliente_autenticado):
    resposta = cliente_autenticado.post(
        URL, {"mes": 10, "ano": 2026, "fechado": True}, format="json"
    )

    assert resposta.status_code == 201
    assert resposta.json()["fechado"] is False
    assert MesReferencia.objects.get().fechado is False


def test_mes_repetido_na_mesma_conta(usuario, cliente_autenticado):
    _mes(usuario)

    resposta = cliente_autenticado.post(URL, {"mes": 10, "ano": 2026}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == MES_REPETIDO
    assert MesReferencia.objects.do_dono(usuario).count() == 1


def test_mesmo_mes_em_outra_conta(usuario, outro_usuario, cliente_autenticado):
    _mes(outro_usuario)

    resposta = cliente_autenticado.post(URL, {"mes": 10, "ano": 2026}, format="json")

    assert resposta.status_code == 201


@pytest.mark.parametrize("mes", [0, 13, "outubro", "10.5"])
def test_mes_invalido(cliente_autenticado, mes):
    resposta = cliente_autenticado.post(URL, {"mes": mes, "ano": 2026}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"mes": MES_INVALIDO}
    assert not MesReferencia.objects.exists()


@pytest.mark.parametrize("ano", [1999, 2101, "dois mil"])
def test_ano_invalido(cliente_autenticado, ano):
    resposta = cliente_autenticado.post(URL, {"mes": 10, "ano": ano}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"ano": ANO_INVALIDO}


def test_mes_e_ano_invalidos_de_uma_vez(cliente_autenticado):
    resposta = cliente_autenticado.post(URL, {"mes": 13, "ano": 1999}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"mes": MES_INVALIDO, "ano": ANO_INVALIDO}


@pytest.mark.parametrize(
    "payload, campo",
    [
        ({"ano": 2026}, "mes"),
        ({"mes": 10}, "ano"),
        ({"mes": "", "ano": 2026}, "mes"),
        ({"mes": 10, "ano": ""}, "ano"),
        ({"mes": None, "ano": 2026}, "mes"),
    ],
)
def test_campo_obrigatorio(cliente_autenticado, payload, campo):
    resposta = cliente_autenticado.post(URL, payload, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {campo: OBRIGATORIO}


def test_criar_sem_sessao(cliente):
    assert cliente.post(URL, {"mes": 10, "ano": 2026}, format="json").status_code == 401


def test_corrida_vira_mes_repetido_e_nao_erro_500(usuario, cliente_autenticado, monkeypatch):
    # Simula dois envios simultâneos: a checagem do serializer não vê o outro, só o banco segura.
    monkeypatch.setattr(MesReferenciaSerializer, "get_validators", lambda self: [])
    _mes(usuario)

    resposta = cliente_autenticado.post(URL, {"mes": 10, "ano": 2026}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == MES_REPETIDO
    assert MesReferencia.objects.do_dono(usuario).count() == 1
