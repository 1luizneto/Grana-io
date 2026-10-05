import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from accounts.models import Usuario

SENHA = "uma-senha-boa-2026"


@pytest.fixture(autouse=True)
def limpar_cache():
    # O limite de tentativas de login guarda a contagem no cache; cada teste começa do zero.
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def usuario(db):
    return Usuario.objects.create_user(email="ana@exemplo.com", nome="Ana Souza", password=SENHA)


@pytest.fixture
def outro_usuario(db):
    return Usuario.objects.create_user(email="bia@exemplo.com", nome="Bia Lima", password=SENHA)


@pytest.fixture
def cliente():
    return APIClient()


@pytest.fixture
def cliente_autenticado(usuario):
    # Autenticação simulada; testes que precisam do JWT real fazem login ou usam AccessToken.
    cliente = APIClient()
    cliente.force_authenticate(user=usuario)
    return cliente


@pytest.fixture
def cliente_da_bia(outro_usuario):
    # Segunda conta, para os testes de isolamento por dono (spec 004).
    cliente = APIClient()
    cliente.force_authenticate(user=outro_usuario)
    return cliente
