from django.conf import settings
from django.db import IntegrityError, transaction

from accounts.models import Usuario


class EmailJaCadastrado(Exception):
    """O e-mail já pertence a uma conta (inclusive quando dois cadastros chegam juntos)."""


def cadastro_aberto() -> bool:
    """Indica se novas contas podem ser criadas (GRANA_CADASTRO_ABERTO, FR-012)."""
    return settings.CADASTRO_ABERTO


def cadastrar_usuario(nome, email, senha) -> Usuario:
    """Cria a conta de forma atômica. Não autentica a pessoa (FR-009)."""
    try:
        with transaction.atomic():
            usuario = Usuario.objects.create_user(email=email, nome=nome, password=senha)
            # US-05: as categorias padrão do usuário serão criadas aqui, por chamada explícita
            # (sem signals), dentro da mesma transação.
            return usuario
    except IntegrityError as erro:
        # Só a restrição única do e-mail pode falhar aqui (FR-004).
        raise EmailJaCadastrado(email) from erro
