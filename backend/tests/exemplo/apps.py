from django.apps import AppConfig


class ExemploConfig(AppConfig):
    """App só de testes, com registros de exemplo para provar o isolamento (spec 004, R-07)."""

    name = "tests.exemplo"
    label = "exemplo"
    default_auto_field = "django.db.models.BigAutoField"
