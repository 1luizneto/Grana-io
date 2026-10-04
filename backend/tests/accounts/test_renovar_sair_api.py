"""Contrato: specs/003-login-logout/contracts/api-sessao.md (renovar e sair)."""

import pytest
from django.test import RequestFactory
from django.views.debug import SafeExceptionReporterFilter

from accounts.services.sessao import emitir_sessao
from accounts.views import RenovarView

URL_RENOVAR = "/api/auth/renovar/"
URL_EU = "/api/usuarios/eu/"
SESSAO_ENCERRADA = {"detail": "Sessão expirada ou encerrada. Entre novamente."}

pytestmark = pytest.mark.django_db


def _renovar(cliente, renovacao):
    return cliente.post(URL_RENOVAR, {"renovacao": renovacao}, format="json")


# --- Renovar (US4) -------------------------------------------------------------------------


def test_renovar_devolve_par_novo_que_funciona(cliente, usuario):
    renovacao = emitir_sessao(usuario)["renovacao"]

    resposta = _renovar(cliente, renovacao)

    assert resposta.status_code == 200
    assert set(resposta.json()) == {"acesso", "renovacao"}
    acesso = resposta.json()["acesso"]
    assert cliente.get(URL_EU, HTTP_AUTHORIZATION=f"Bearer {acesso}").status_code == 200


def test_renovacao_usada_de_novo_e_recusada(cliente, usuario):
    renovacao = emitir_sessao(usuario)["renovacao"]
    _renovar(cliente, renovacao)

    resposta = _renovar(cliente, renovacao)

    assert resposta.status_code == 401
    assert resposta.json() == SESSAO_ENCERRADA


def test_renovacao_adulterada_e_recusada(cliente):
    resposta = _renovar(cliente, "abc.def.ghi")

    assert resposta.status_code == 401
    assert resposta.json() == SESSAO_ENCERRADA


def test_renovar_sem_campo(cliente):
    resposta = cliente.post(URL_RENOVAR, {}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"renovacao": ["Este campo é obrigatório."]}


def test_renovacao_mascarada_na_pagina_de_erro(usuario):
    request = RequestFactory().post(URL_RENOVAR, data={"renovacao": emitir_sessao(usuario)["renovacao"]})

    RenovarView.as_view()(request)

    assert SafeExceptionReporterFilter().get_post_parameters(request)["renovacao"] == "********************"
