import pytest
from django.db import OperationalError, connection

from core.services.saude import verificar_banco


@pytest.mark.django_db
def test_retorna_true_com_banco_acessivel():
    assert verificar_banco() is True


def test_retorna_false_quando_banco_falha(monkeypatch):
    def cursor_quebrado(*args, **kwargs):
        raise OperationalError("connection refused: host=db user=grana")

    monkeypatch.setattr(connection, "cursor", cursor_quebrado)

    assert verificar_banco() is False
