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
