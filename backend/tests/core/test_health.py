"""Contrato: specs/001-infra-docker/contracts/api-health.md"""

import pytest
from rest_framework.test import APIClient

URL = "/api/health/"


@pytest.fixture
def cliente():
    # Sem autenticação: a rota de saúde é pública (FR-007).
    return APIClient()


@pytest.mark.django_db
def test_banco_ok_retorna_200(cliente):
    resposta = cliente.get(URL)

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "database": "ok"}


def test_banco_indisponivel_retorna_503_sem_detalhes(cliente, monkeypatch):
    monkeypatch.setattr("core.views.verificar_banco", lambda: False)

    resposta = cliente.get(URL)

    assert resposta.status_code == 503
    # Corpo exato: nenhuma chave extra, mensagem de exceção, host ou credencial.
    assert resposta.json() == {"status": "error", "database": "unavailable"}


def test_post_nao_permitido(cliente):
    resposta = cliente.post(URL)

    assert resposta.status_code == 405
