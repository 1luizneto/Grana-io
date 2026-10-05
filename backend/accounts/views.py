from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import (
    MENSAGEM_EMAIL_DUPLICADO,
    CadastroSerializer,
    EntrarSerializer,
    RenovacaoSerializer,
    UsuarioSerializer,
)
from accounts.services.cadastro import EmailJaCadastrado, cadastrar_usuario, cadastro_aberto
from accounts.services.sessao import (
    SessaoInvalida,
    autenticar,
    emitir_sessao,
    encerrar_sessao,
    renovar_sessao,
)
from accounts.throttles import MuitasTentativas, TentativasLoginThrottle

MENSAGEM_CADASTRO_FECHADO = "O cadastro de novas contas está desativado neste sistema."
MENSAGEM_CREDENCIAIS_INVALIDAS = "E-mail ou senha incorretos."
MENSAGEM_SESSAO_ENCERRADA = "Sessão expirada ou encerrada. Entre novamente."
MENSAGEM_SESSAO_INVALIDA = "Sessão inválida ou já encerrada."


@method_decorator(sensitive_post_parameters("senha", "confirmacao_senha"), name="dispatch")
class CadastroView(APIView):
    """Cadastro público de usuário (specs/002-cadastro-usuario/contracts/api-cadastro.md)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ["post", "options"]

    def post(self, request):
        if not cadastro_aberto():
            return Response({"detail": MENSAGEM_CADASTRO_FECHADO}, status=status.HTTP_403_FORBIDDEN)

        serializer = CadastroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data
        try:
            usuario = cadastrar_usuario(nome=dados["nome"], email=dados["email"], senha=dados["senha"])
        except EmailJaCadastrado:
            return Response({"email": [MENSAGEM_EMAIL_DUPLICADO]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)


@method_decorator(sensitive_post_parameters("senha"), name="dispatch")
class EntrarView(APIView):
    """Login por e-mail e senha (specs/003-login-logout/contracts/api-sessao.md)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [TentativasLoginThrottle]
    http_method_names = ["post", "options"]

    def throttled(self, request, wait):
        raise MuitasTentativas(wait=wait)

    def post(self, request):
        serializer = EntrarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data
        usuario = autenticar(email=dados["email"], senha=dados["senha"], request=request)
        if usuario is None:
            return Response(
                {"detail": MENSAGEM_CREDENCIAIS_INVALIDAS}, status=status.HTTP_401_UNAUTHORIZED
            )
        return Response({**emitir_sessao(usuario), "usuario": UsuarioSerializer(usuario).data})


class EuView(APIView):
    """Dados da própria conta; exige credencial de acesso (permissão padrão)."""

    http_method_names = ["get", "head", "options"]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


@method_decorator(sensitive_post_parameters("renovacao"), name="dispatch")
class RenovarView(APIView):
    """Renovação de uso único da sessão (specs/003-login-logout/contracts/api-sessao.md)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ["post", "options"]

    def post(self, request):
        serializer = RenovacaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            sessao = renovar_sessao(serializer.validated_data["renovacao"])
        except SessaoInvalida:
            return Response({"detail": MENSAGEM_SESSAO_ENCERRADA}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(sessao)


@method_decorator(sensitive_post_parameters("renovacao"), name="dispatch")
class SairView(APIView):
    """Encerra a sessão do próprio usuário; exige credencial de acesso (contracts/api-sessao.md)."""

    http_method_names = ["post", "options"]

    def post(self, request):
        serializer = RenovacaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            encerrar_sessao(request.user, serializer.validated_data["renovacao"])
        except SessaoInvalida:
            return Response({"renovacao": [MENSAGEM_SESSAO_INVALIDA]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
