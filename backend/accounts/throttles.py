"""Limite de tentativas de login por endereço de origem (FR-015; research R-07, R-08)."""

import math
import socket
import time

from django.conf import settings
from rest_framework.exceptions import Throttled
from rest_framework.throttling import SimpleRateThrottle

MENSAGEM_MUITAS_TENTATIVAS = "Muitas tentativas. Tente novamente em instantes."

_CACHE_PROXY_SEGUNDOS = 60
_proxy_resolvido = {"ip": None, "em": 0.0}


def ip_do_proxy_confiavel():
    """IP atual do proxy da interface (serviço `frontend`), ou None se não resolver."""
    agora = time.monotonic()
    if agora - _proxy_resolvido["em"] > _CACHE_PROXY_SEGUNDOS:
        try:
            _proxy_resolvido["ip"] = socket.gethostbyname(settings.PROXY_CONFIAVEL)
        except OSError:
            _proxy_resolvido["ip"] = None
        _proxy_resolvido["em"] = agora
    return _proxy_resolvido["ip"]


def _normalizar(endereco):
    """Remove o prefixo IPv6 que o Node (proxy do Vite) põe em clientes IPv4 ("::ffff:a.b.c.d")."""
    if endereco and endereco.lower().startswith("::ffff:"):
        return endereco[len("::ffff:"):]
    return endereco


class MuitasTentativas(Throttled):
    """429 com a mensagem da spec, sem o sufixo de segundos; o wait vai para o Retry-After."""

    def __init__(self, wait=None):
        super().__init__(detail=MENSAGEM_MUITAS_TENTATIVAS)
        self.wait = math.ceil(wait) if wait is not None else None


class TentativasLoginThrottle(SimpleRateThrottle):
    scope = "login"

    def get_rate(self):
        # Lido a cada requisição (e não de DEFAULT_THROTTLE_RATES) para respeitar a configuração
        # vigente, inclusive override_settings nos testes.
        return f"{settings.LOGIN_TENTATIVAS_POR_MINUTO}/min"

    def get_ident(self, request):
        # Só confia no X-Forwarded-For quando a requisição vem do proxy da interface; acesso direto
        # à API não consegue trocar de "dispositivo" forjando o cabeçalho.
        origem = _normalizar(request.META.get("REMOTE_ADDR"))
        encaminhado = request.META.get("HTTP_X_FORWARDED_FOR")
        if encaminhado and origem and origem == ip_do_proxy_confiavel():
            return _normalizar(encaminhado.split(",")[-1].strip())
        return origem

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
