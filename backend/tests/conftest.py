import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def limpar_cache():
    # O limite de tentativas de login guarda a contagem no cache; cada teste começa do zero.
    cache.clear()
    yield
    cache.clear()
