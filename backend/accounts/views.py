from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import (
    MENSAGEM_EMAIL_DUPLICADO,
    CadastroSerializer,
    UsuarioCadastradoSerializer,
)
from accounts.services.cadastro import EmailJaCadastrado, cadastrar_usuario, cadastro_aberto

MENSAGEM_CADASTRO_FECHADO = "O cadastro de novas contas está desativado neste sistema."


@method_decorator(sensitive_post_parameters("senha", "confirmacao_senha"), name="dispatch")
class CadastroView(APIView):
    """Cadastro público de usuário (contracts/api-cadastro.md)."""

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
        return Response(UsuarioCadastradoSerializer(usuario).data, status=status.HTTP_201_CREATED)
