from django.db import models
from django.db.models.functions import Collate, Lower

from core.models import OwnedModel
from gastos.cores import CHOICES

# Ordenação alfabética que respeita acentos ("Água" antes de "Banco"). A collation padrão do banco
# (libc, en_US.utf8 no Alpine) põe as letras acentuadas depois do "z" (research R-10).
ORDEM_ALFABETICA = Collate(Lower("nome"), "und-x-icu")


class Categoria(OwnedModel):
    """Categoria de gasto de uma pessoa (US-05; specs/006-categorias-gasto/data-model.md)."""

    nome = models.CharField(max_length=50)
    cor = models.CharField(max_length=20, choices=CHOICES)

    class Meta:
        ordering = [ORDEM_ALFABETICA]
        constraints = [
            # Nome único por pessoa, sem diferenciar maiúsculas (acentos contam).
            models.UniqueConstraint(
                Lower("nome"),
                "dono",
                name="gastos_categoria_nome_por_dono",
                violation_error_message="Já existe uma categoria com este nome.",
            )
        ]

    def __str__(self):
        return self.nome


class MesReferencia(OwnedModel):
    """Mês de referência de uma pessoa (US-06; specs/007-mes-referencia/data-model.md).

    Mês e ano são definidos na criação e não mudam; a única alteração é fechar ou reabrir.
    """

    mes = models.PositiveSmallIntegerField()
    ano = models.PositiveSmallIntegerField()
    fechado = models.BooleanField(default=False)

    class Meta:
        # Dois inteiros dão a ordem cronológica direto (research R-01).
        ordering = ["ano", "mes"]
        constraints = [
            # As faixas valem também fora da API (shell, migrations de dados).
            models.CheckConstraint(
                condition=models.Q(mes__gte=1, mes__lte=12), name="gastos_mes_mes_valido"
            ),
            models.CheckConstraint(
                condition=models.Q(ano__gte=2000, ano__lte=2100), name="gastos_mes_ano_valido"
            ),
            models.UniqueConstraint(
                fields=["dono", "ano", "mes"],
                name="gastos_mes_unico_por_dono",
                violation_error_message="Este mês já foi criado.",
            ),
        ]

    @property
    def rotulo(self):
        """Forma MM/AAAA exibida na interface (research R-06)."""
        return f"{self.mes:02d}/{self.ano}"

    def __str__(self):
        return self.rotulo


# Formas de pagamento aceitas (US-07; specs/008-lancar-gastos/research.md, R-08).
FORMAS_PAGAMENTO = [
    ("dinheiro", "Dinheiro"),
    ("debito", "Débito"),
    ("credito", "Crédito"),
    ("pix", "Pix"),
]


class GastoFixo(OwnedModel):
    """Gasto fixo: modelo que gera um gasto em cada mês novo (US-07b;
    specs/010-gastos-fixos/data-model.md). Meses já existentes nunca mudam por causa dele.
    """

    descricao = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    forma_pagamento = models.CharField(
        max_length=10, choices=FORMAS_PAGAMENTO, blank=True, default=""
    )
    categoria = models.ForeignKey(Categoria, on_delete=models.RESTRICT, related_name="fixos")
    dia_vencimento = models.PositiveSmallIntegerField()
    # Meses guardados como o dia 1; fim nulo = sem fim.
    inicio = models.DateField()
    fim = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["dia_vencimento", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(valor__gt=0), name="gastos_fixo_valor_positivo"
            ),
            models.CheckConstraint(
                condition=models.Q(dia_vencimento__gte=1, dia_vencimento__lte=31),
                name="gastos_fixo_dia_valido",
            ),
            models.CheckConstraint(
                condition=models.Q(fim__isnull=True) | models.Q(fim__gte=models.F("inicio")),
                name="gastos_fixo_fim_depois_do_inicio",
            ),
        ]

    def __str__(self):
        return self.descricao


class Gasto(OwnedModel):
    """Gasto de uma pessoa num mês de referência (US-07; specs/008-lancar-gastos/data-model.md).

    ``RESTRICT`` em mês e categoria: nenhum dos dois se exclui com gastos, mas a exclusão da conta
    apaga tudo em cascata (o RESTRICT libera quando o gasto também está sendo apagado).
    """

    descricao = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField()
    forma_pagamento = models.CharField(
        max_length=10, choices=FORMAS_PAGAMENTO, blank=True, default=""
    )
    mes = models.ForeignKey(MesReferencia, on_delete=models.RESTRICT, related_name="gastos")
    categoria = models.ForeignKey(Categoria, on_delete=models.RESTRICT, related_name="gastos")
    # Gasto fixo de origem (US-07b): excluir o fixo mantém o gasto, como gasto comum.
    fixo = models.ForeignKey(
        GastoFixo,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="gastos_gerados",
    )

    class Meta:
        ordering = ["data", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(valor__gt=0), name="gastos_gasto_valor_positivo"
            ),
        ]

    def __str__(self):
        return self.descricao
