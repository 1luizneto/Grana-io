"""Sessão por JWT (specs/003-login-logout). Único ponto que usa o simplejwt diretamente."""

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Usuario


def autenticar(email, senha, request=None) -> Usuario | None:
    """Usuário ativo com essas credenciais, ou None (e-mail inexistente, senha errada ou conta
    desativada recebem o mesmo tratamento; research R-03)."""
    return authenticate(request, email=email, password=senha)


def emitir_sessao(usuario) -> dict:
    """Credenciais de acesso e de renovação; registra o último acesso (FR-005)."""
    renovacao = RefreshToken.for_user(usuario)
    update_last_login(None, usuario)
    return {"acesso": str(renovacao.access_token), "renovacao": str(renovacao)}
