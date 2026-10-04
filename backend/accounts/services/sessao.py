"""Sessão por JWT (specs/003-login-logout). Único ponto que usa o simplejwt diretamente."""

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Usuario


class SessaoInvalida(Exception):
    """Credencial de renovação vencida, adulterada, já usada, encerrada ou de conta desativada."""


def autenticar(email, senha, request=None) -> Usuario | None:
    """Usuário ativo com essas credenciais, ou None (e-mail inexistente, senha errada ou conta
    desativada recebem o mesmo tratamento; research R-03)."""
    return authenticate(request, email=email, password=senha)


def emitir_sessao(usuario) -> dict:
    """Credenciais de acesso e de renovação; registra o último acesso (FR-005)."""
    renovacao = RefreshToken.for_user(usuario)
    update_last_login(None, usuario)
    return {"acesso": str(renovacao.access_token), "renovacao": str(renovacao)}


def renovar_sessao(renovacao) -> dict:
    """Troca a credencial de renovação por um par novo; a usada fica bloqueada (FR-007, FR-008).

    Reaproveita o serializer do simplejwt, que valida, recusa conta desativada, gira e bloqueia
    a credencial antiga na ordem correta (research R-04).
    """
    serializer = TokenRefreshSerializer(data={"refresh": renovacao})
    try:
        serializer.is_valid(raise_exception=True)
    except (TokenError, InvalidToken, AuthenticationFailed, ValidationError) as erro:
        raise SessaoInvalida from erro
    return {"acesso": serializer.validated_data["access"], "renovacao": serializer.validated_data["refresh"]}
