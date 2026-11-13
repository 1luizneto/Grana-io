"""Regras de gastos que cruzam gasto, mês e categoria (specs/008-lancar-gastos/research.md, R-03).

As funções recebem e devolvem objetos Python e sinalizam regra violada com ``RegraViolada``; as
views traduzem para a resposta HTTP.
"""


class RegraViolada(Exception):
    """Regra de negócio violada; a mensagem é exibida para a pessoa como está."""


def exigir_mes_aberto(*meses):
    """Recusa mudanças em gastos de mês fechado (FR-008). ``None`` é ignorado."""
    for mes in meses:
        if mes is not None and mes.fechado:
            raise RegraViolada(
                f"O mês {mes.rotulo} está fechado. Reabra o mês para alterar os gastos."
            )
