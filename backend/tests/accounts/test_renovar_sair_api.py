"""Contrato: specs/003-login-logout/contracts/api-sessao.md (renovar e sair)."""

import pytest
from django.test import RequestFactory
from django.views.debug import SafeExceptionReporterFilter
from rest_framework.test import force_authenticate

from accounts.services.sessao import emitir_sessao
from accounts.views import RenovarView, SairView

URL_RENOVAR = "/api/auth/renovar/"
URL_SAIR = "/api/auth/sair/"
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


# --- Sair (US5) ----------------------------------------------------------------------------

SESSAO_INVALIDA = {"renovacao": ["Sessão inválida ou já encerrada."]}


def _sair(cliente, acesso, renovacao):
    return cliente.post(
        URL_SAIR, {"renovacao": renovacao}, format="json", HTTP_AUTHORIZATION=f"Bearer {acesso}"
    )


def test_sair_encerra_so_a_sessao_informada(cliente, usuario):
    sessao_a = emitir_sessao(usuario)
    sessao_b = emitir_sessao(usuario)

    resposta = _sair(cliente, sessao_a["acesso"], sessao_a["renovacao"])

    assert resposta.status_code == 204
    assert _renovar(cliente, sessao_a["renovacao"]).status_code == 401
    assert _renovar(cliente, sessao_b["renovacao"]).status_code == 200


def test_sair_exige_credencial_de_acesso(cliente, usuario):
    renovacao = emitir_sessao(usuario)["renovacao"]

    resposta = cliente.post(URL_SAIR, {"renovacao": renovacao}, format="json")

    assert resposta.status_code == 401
    assert _renovar(cliente, renovacao).status_code == 200


def test_sair_com_renovacao_de_outra_pessoa_e_recusado(cliente, usuario, outro_usuario):
    da_ana = emitir_sessao(usuario)
    da_bia = emitir_sessao(outro_usuario)

    resposta = _sair(cliente, da_bia["acesso"], da_ana["renovacao"])

    assert resposta.status_code == 400
    assert resposta.json() == SESSAO_INVALIDA
    assert _renovar(cliente, da_ana["renovacao"]).status_code == 200


def test_sair_sem_campo(cliente, usuario):
    acesso = emitir_sessao(usuario)["acesso"]

    resposta = cliente.post(URL_SAIR, {}, format="json", HTTP_AUTHORIZATION=f"Bearer {acesso}")

    assert resposta.status_code == 400
    assert resposta.json() == {"renovacao": ["Este campo é obrigatório."]}


def test_renovacao_mascarada_na_pagina_de_erro_ao_sair(usuario):
    request = RequestFactory().post(URL_SAIR, data={"renovacao": emitir_sessao(usuario)["renovacao"]})
    force_authenticate(request, user=usuario)

    SairView.as_view()(request)

    assert SafeExceptionReporterFilter().get_post_parameters(request)["renovacao"] == "********************"
