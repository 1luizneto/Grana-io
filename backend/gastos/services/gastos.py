"""Regras de gastos que cruzam gasto, mês e categoria (specs/008-lancar-gastos/research.md, R-03).

As funções recebem e devolvem objetos Python e sinalizam regra violada com ``RegraViolada``; as
views traduzem para a resposta HTTP.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Sum
from django.db.models.functions import Collate, Lower

from core.dinheiro import arredondar


class RegraViolada(Exception):
    """Regra de negócio violada; a mensagem é exibida para a pessoa como está."""


def exigir_mes_aberto(*meses):
    """Recusa mudanças em gastos de mês fechado (FR-008). ``None`` é ignorado."""
    for mes in meses:
        if mes is not None and mes.fechado:
            raise RegraViolada(
                f"O mês {mes.rotulo} está fechado. Reabra o mês para alterar os gastos."
            )


def verificar_exclusao_do_mes(mes):
    """Mês fechado (spec 007) e mês com gastos (FR-009) não se excluem."""
    if mes.fechado:
        raise RegraViolada("Reabra o mês antes de excluí-lo.")
    if mes.gastos.exists():
        raise RegraViolada("Exclua ou mova os gastos antes de excluir o mês.")


@transaction.atomic
def excluir_categoria(categoria, destino):
    """Exclui a categoria; os gastos dela passam antes para ``destino`` (FR-010; research R-07).

    ``destino`` já vem conferido pela view (da mesma pessoa e diferente de ``categoria``). Gastos
    de meses fechados também mudam de categoria: o total do mês não muda (Clarifications). Os
    gastos fixos da categoria contam como gastos e vão junto (spec 010, R-05).
    """
    gastos, fixos = categoria.gastos.all(), categoria.fixos.all()
    if gastos.exists() or fixos.exists():
        if destino is None:
            raise RegraViolada(
                "Esta categoria tem gastos. Escolha outra categoria para recebê-los."
            )
        gastos.update(categoria=destino)
        fixos.update(categoria=destino)
    categoria.delete()


@dataclass
class TotalDaCategoria:
    categoria: int
    nome: str
    cor: str
    total: Decimal
    quantidade: int


@dataclass
class TotaisDoMes:
    total: Decimal
    por_categoria: list[TotalDaCategoria] = field(default_factory=list)


def totais_do_mes(mes):
    """Total do mês e de cada categoria com gastos nele (FR-006; research R-06).

    Soma em ``Decimal`` no banco; maior total primeiro e, empatando, ordem alfabética com acentos.
    """
    linhas = (
        mes.gastos.values("categoria", "categoria__nome", "categoria__cor")
        .annotate(total=Sum("valor"), quantidade=Count("id"))
        .order_by("-total", Collate(Lower("categoria__nome"), "und-x-icu"))
    )
    por_categoria = [
        TotalDaCategoria(
            categoria=linha["categoria"],
            nome=linha["categoria__nome"],
            cor=linha["categoria__cor"],
            total=arredondar(linha["total"]),
            quantidade=linha["quantidade"],
        )
        for linha in linhas
    ]
    total = sum((item.total for item in por_categoria), Decimal(0))
    return TotaisDoMes(total=arredondar(total), por_categoria=por_categoria)
