"""Settings da suíte de testes (specs/004-isolamento-usuario/research.md, R-07).

Acrescenta o app de exemplo, que existe só no banco de testes para provar o isolamento por dono.
O ``settings.py`` de uso nunca inclui esse app.
"""

from config.settings import *  # noqa: F403

INSTALLED_APPS = [*INSTALLED_APPS, "tests.exemplo"]  # noqa: F405
