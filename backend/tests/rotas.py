"""Percorre a árvore de rotas do Django; usado pelas guardas de proteção (spec 003) e de isolamento (spec 004)."""

from django.urls import URLPattern, URLResolver


def rotas(padroes, prefixo=""):
    """Gera ``(caminho, padrao)`` para cada rota final, descendo pelos ``include``."""
    for padrao in padroes:
        if isinstance(padrao, URLResolver):
            yield from rotas(padrao.url_patterns, prefixo + str(padrao.pattern))
        elif isinstance(padrao, URLPattern):
            yield prefixo + str(padrao.pattern), padrao
