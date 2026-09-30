from django.db import Error, connection


def verificar_banco() -> bool:
    """Indica se o banco responde. Não propaga nem expõe detalhes da falha (FR-007)."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Error:
        return False
