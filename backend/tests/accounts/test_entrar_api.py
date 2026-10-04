"""Contrato: specs/003-login-logout/contracts/api-sessao.md"""

import pytest
from django.test import RequestFactory
from django.views.debug import SafeExceptionReporterFilter

from accounts.views import EntrarView
from tests.accounts.conftest import SENHA

URL_ENTRAR = "/api/auth/entrar/"
URL_EU = "/api/usuarios/eu/"

pytestmark = pytest.mark.django_db


def test_entrar_devolve_credenciais_e_dados_da_conta(cliente, usuario):
    resposta = cliente.post(URL_ENTRAR, {"email": " ANA@Exemplo.com ", "senha": SENHA}, format="json")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert set(corpo) == {"acesso", "renovacao", "usuario"}
    assert corpo["usuario"] == {"nome": "Ana Souza", "email": "ana@exemplo.com"}
    assert SENHA not in resposta.content.decode()


def test_credencial_de_acesso_permite_consultar_a_propria_conta(cliente, usuario):
    acesso = cliente.post(URL_ENTRAR, {"email": "ana@exemplo.com", "senha": SENHA}, format="json").json()["acesso"]

    resposta = cliente.get(URL_EU, HTTP_AUTHORIZATION=f"Bearer {acesso}")

    assert resposta.status_code == 200
    assert resposta.json() == {"nome": "Ana Souza", "email": "ana@exemplo.com"}


def test_senha_mascarada_na_pagina_de_erro(usuario):
    request = RequestFactory().post(URL_ENTRAR, data={"email": "ana@exemplo.com", "senha": SENHA})

    EntrarView.as_view()(request)

    parametros = SafeExceptionReporterFilter().get_post_parameters(request)
    assert parametros["senha"] == "********************"
    assert parametros["email"] == "ana@exemplo.com"
