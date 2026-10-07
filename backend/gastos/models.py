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
