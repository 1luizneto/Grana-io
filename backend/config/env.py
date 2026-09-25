"""Leitura de configuração a partir de variáveis de ambiente (12-factor)."""

import os

# Chave usada só no modo de desenvolvimento, quando DJANGO_SECRET_KEY não é definida.
CHAVE_DEV_PADRAO = "django-insecure-grana-dev-troque-me"

_VERDADEIROS = {"1", "true", "yes", "on"}


def env_str(nome, padrao=""):
    return os.environ.get(nome, padrao)


def env_bool(nome, padrao=False):
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in _VERDADEIROS


def env_list(nome):
    valor = os.environ.get(nome, "")
    return [item.strip() for item in valor.split(",") if item.strip()]
