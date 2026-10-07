from django.apps import AppConfig


class GastosConfig(AppConfig):
    """Categorias, meses e gastos (EP-02; specs/006-categorias-gasto, research R-01)."""

    name = "gastos"
    default_auto_field = "django.db.models.BigAutoField"
