"""Guarda de regressão: nenhum model alterado sem migration (Definition of Done).

Não há implementação associada, então o ciclo Red-Green não se aplica; o teste passa desde já e
protege as próximas specs.
"""

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_nao_ha_migrations_pendentes():
    call_command("makemigrations", "--check", "--dry-run", verbosity=0)
