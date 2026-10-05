"""Limite de tentativas de login (FR-015; research R-07, R-08)."""

import pytest
from django.test import RequestFactory, override_settings

from accounts.throttles import TentativasLoginThrottle
from tests.conftest import SENHA

URL = "/api/auth/entrar/"
MENSAGEM = {"detail": "Muitas tentativas. Tente novamente em instantes."}
IP_PROXY = "172.20.0.5"

pytestmark = pytest.mark.django_db


@pytest.fixture
def proxy_confiavel(monkeypatch):
    monkeypatch.setattr("accounts.throttles.ip_do_proxy_confiavel", lambda: IP_PROXY)


def _tentar(cliente, senha="senha-errada-123", **extra):
    return cliente.post(URL, {"email": "ana@exemplo.com", "senha": senha}, format="json", **extra)


@override_settings(LOGIN_TENTATIVAS_POR_MINUTO=3)
def test_quarta_tentativa_no_minuto_e_recusada_mesmo_com_senha_certa(cliente, usuario):
    for _ in range(3):
        assert _tentar(cliente).status_code == 401

    resposta = _tentar(cliente, senha=SENHA)

    assert resposta.status_code == 429
    assert resposta.json() == MENSAGEM
    assert int(resposta.headers["Retry-After"]) > 0


@override_settings(LOGIN_TENTATIVAS_POR_MINUTO=3)
def test_dispositivos_atras_do_proxy_tem_contagens_separadas(cliente, usuario, proxy_confiavel):
    celular = {"REMOTE_ADDR": IP_PROXY, "HTTP_X_FORWARDED_FOR": "192.168.1.50"}
    notebook = {"REMOTE_ADDR": IP_PROXY, "HTTP_X_FORWARDED_FOR": "192.168.1.60"}

    for _ in range(3):
        _tentar(cliente, **celular)

    assert _tentar(cliente, **celular).status_code == 429
    assert _tentar(cliente, **notebook).status_code == 401


def test_usa_ultimo_endereco_do_cabecalho_quando_vem_do_proxy(proxy_confiavel):
    request = RequestFactory().post(
        URL, REMOTE_ADDR=IP_PROXY, HTTP_X_FORWARDED_FOR="10.0.0.7, 192.168.1.50"
    )

    assert TentativasLoginThrottle().get_ident(request) == "192.168.1.50"


def test_ignora_cabecalho_forjado_fora_do_proxy(proxy_confiavel):
    request = RequestFactory().post(
        URL, REMOTE_ADDR="192.168.1.99", HTTP_X_FORWARDED_FOR="1.2.3.4"
    )

    assert TentativasLoginThrottle().get_ident(request) == "192.168.1.99"


def test_sem_proxy_resolvido_usa_endereco_de_origem(monkeypatch):
    monkeypatch.setattr("accounts.throttles.ip_do_proxy_confiavel", lambda: None)
    request = RequestFactory().post(URL, REMOTE_ADDR=IP_PROXY, HTTP_X_FORWARDED_FOR="1.2.3.4")

    assert TentativasLoginThrottle().get_ident(request) == IP_PROXY


def test_normaliza_endereco_ipv4_no_formato_ipv6_do_node(proxy_confiavel):
    # O Vite (Node) escuta em IPv6 e encaminha clientes IPv4 como "::ffff:a.b.c.d"; sem normalizar,
    # o mesmo dispositivo contaria em dobro (pelo proxy e direto na API).
    pelo_proxy = RequestFactory().post(
        URL, REMOTE_ADDR=IP_PROXY, HTTP_X_FORWARDED_FOR="::ffff:192.168.1.50"
    )
    direto = RequestFactory().post(URL, REMOTE_ADDR="192.168.1.50")

    throttle = TentativasLoginThrottle()
    assert throttle.get_ident(pelo_proxy) == "192.168.1.50"
    assert throttle.get_ident(pelo_proxy) == throttle.get_ident(direto)
