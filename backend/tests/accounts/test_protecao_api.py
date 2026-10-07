"""Proteção das rotas (FR-010, FR-011, FR-012, FR-014; contracts/api-sessao.md)."""

from datetime import timedelta

import pytest
from django.urls import get_resolver
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken

from tests.rotas import rotas

URL_EU = "/api/usuarios/eu/"
ROTAS_PUBLICAS = {"saude", "cadastro", "entrar", "renovar"}

pytestmark = pytest.mark.django_db


def _bearer(token):
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def test_sem_credencial_e_recusado(cliente):
    resposta = cliente.get(URL_EU)

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "As credenciais de autenticação não foram fornecidas."
    assert resposta.headers["WWW-Authenticate"].startswith("Bearer")


def test_credencial_adulterada_e_recusada(cliente):
    resposta = cliente.get(URL_EU, **_bearer("abc.def.ghi"))

    assert resposta.status_code == 401
    assert resposta.json()["code"] == "token_not_valid"


def test_credencial_vencida_e_distinguivel(cliente, usuario):
    token = AccessToken.for_user(usuario)
    token.set_exp(lifetime=-timedelta(seconds=1))

    resposta = cliente.get(URL_EU, **_bearer(token))

    assert resposta.status_code == 401
    assert resposta.json()["code"] == "token_not_valid"


def test_conta_desativada_perde_o_acesso(cliente, usuario):
    token = AccessToken.for_user(usuario)
    usuario.is_active = False
    usuario.save()

    resposta = cliente.get(URL_EU, **_bearer(token))

    assert resposta.status_code == 401
    assert resposta.json()["code"] == "user_inactive"


def test_cada_credencial_ve_so_a_propria_conta(cliente, usuario, outro_usuario):
    da_ana = cliente.get(URL_EU, **_bearer(AccessToken.for_user(usuario))).json()
    da_bia = cliente.get(URL_EU, **_bearer(AccessToken.for_user(outro_usuario))).json()

    assert da_ana == {"nome": "Ana Souza", "email": "ana@exemplo.com"}
    assert da_bia == {"nome": "Bia Lima", "email": "bia@exemplo.com"}


@pytest.mark.parametrize(
    "metodo,url",
    [("get", "/api/health/"), ("post", "/api/usuarios/"), ("post", "/api/auth/entrar/")],
)
def test_rotas_publicas_nao_exigem_credencial(cliente, metodo, url):
    assert getattr(cliente, metodo)(url, {}, format="json").status_code != 401


def test_guarda_toda_rota_nao_publica_exige_autenticacao():
    # Uma rota nova sem proteção quebra este teste (RNF-02: autenticação em todas as rotas,
    # exceto as públicas declaradas).
    desprotegidas = []
    for caminho, padrao in rotas(get_resolver().url_patterns):
        if padrao.name in ROTAS_PUBLICAS:
            continue
        # APIView expõe a classe em view_class; viewsets do router, em cls.
        view = getattr(padrao.callback, "cls", None) or getattr(padrao.callback, "view_class", None)
        permissoes = getattr(view, "permission_classes", [])
        autenticacoes = getattr(view, "authentication_classes", [])
        if IsAuthenticated not in permissoes or not autenticacoes:
            desprotegidas.append(caminho)

    assert desprotegidas == []
