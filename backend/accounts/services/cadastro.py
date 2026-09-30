from django.conf import settings
from django.db import transaction

from accounts.models import Usuario


def cadastro_aberto() -> bool:
    """Indica se novas contas podem ser criadas (GRANA_CADASTRO_ABERTO, FR-012)."""
    return settings.CADASTRO_ABERTO


def cadastrar_usuario(nome, email, senha) -> Usuario:
    """Cria a conta de forma atômica. Não autentica a pessoa (FR-009)."""
    with transaction.atomic():
        usuario = Usuario.objects.create_user(email=email, nome=nome, password=senha)
        # US-05: as categorias padrão do usuário serão criadas aqui, por chamada explícita
        # (sem signals), dentro da mesma transação.
        return usuario
