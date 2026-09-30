from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.services.saude import verificar_banco


class SaudeView(APIView):
    """Verificação de saúde pública (contracts/api-health.md)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        if verificar_banco():
            return Response({"status": "ok", "database": "ok"})
        return Response(
            {"status": "error", "database": "unavailable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
