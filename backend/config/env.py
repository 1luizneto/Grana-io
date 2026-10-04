"""Leitura de configuração a partir de variáveis de ambiente (12-factor)."""

import os

from django.core.exceptions import ImproperlyConfigured

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


def env_int(nome, padrao):
    """Inteiro ≥ 1 vindo do ambiente; ausente ou vazio usa o padrão."""
    valor = os.environ.get(nome, "").strip()
    if not valor:
        return padrao
    try:
        numero = int(valor)
    except ValueError:
        numero = 0
    if numero < 1:
        raise ImproperlyConfigured(f"A variável {nome} deve ser um número inteiro maior que zero.")
    return numero


def env_list(nome):
    valor = os.environ.get(nome, "")
    return [item.strip() for item in valor.split(",") if item.strip()]


def validar_secret_key(secret_key, debug):
    """Impede subir fora do modo de desenvolvimento com a chave padrão ou vazia (FR-012)."""
    if not debug and secret_key in ("", CHAVE_DEV_PADRAO):
        raise ImproperlyConfigured(
            "Defina a variável DJANGO_SECRET_KEY com uma chave própria: a chave padrão de "
            "desenvolvimento só é aceita com DJANGO_DEBUG=1."
        )
