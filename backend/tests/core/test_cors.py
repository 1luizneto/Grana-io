"""FR-013: CORS fechado por padrão; origens extras só por configuração."""

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

URL = "/api/health/"


@pytest.mark.django_db
def test_origem_externa_nao_recebe_permissao_cors():
    resposta = APIClient().get(URL, HTTP_ORIGIN="http://site-externo.example")

    assert "Access-Control-Allow-Origin" not in resposta.headers


@pytest.mark.django_db
@override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:3000"])
def test_origem_configurada_recebe_permissao_cors():
    resposta = APIClient().get(URL, HTTP_ORIGIN="http://localhost:3000")

    assert resposta.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
