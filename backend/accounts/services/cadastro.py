from django.conf import settings
from django.db import IntegrityError, transaction

from accounts.models import Usuario
from gastos.services.categorias import criar_categorias_padrao


class EmailJaCadastrado(Exception):
    """O e-mail já pertence a uma conta (inclusive quando dois cadastros chegam juntos)."""


def cadastro_aberto() -> bool:
    """Indica se novas contas podem ser criadas (GRANA_CADASTRO_ABERTO, FR-012)."""
    return settings.CADASTRO_ABERTO


@transaction.atomic
def cadastrar_usuario(nome, email, senha) -> Usuario:
    """Cria a conta e as categorias padrão de forma atômica. Não autentica a pessoa (FR-009)."""
    try:
        with transaction.atomic():
            usuario = Usuario.objects.create_user(email=email, nome=nome, password=senha)
    except IntegrityError as erro:
        # Só a restrição única do e-mail pode falhar aqui (FR-004).
        raise EmailJaCadastrado(email) from erro
    # Chamada explícita, sem signals (docs/arquitetura.md §5), fora do except acima: uma falha aqui
    # desfaz a conta e não vira "e-mail já cadastrado" (specs/006-categorias-gasto, research R-04).
    criar_categorias_padrao(usuario)
    return usuario
