"""Registros de exemplo, só no banco de testes (spec 004, FR-013; data-model.md)."""

from django.db import models

from core.models import OwnedModel


class GrupoExemplo(OwnedModel):
    nome = models.CharField(max_length=60)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["dono", "nome"],
                name="exemplo_grupo_nome_por_dono",
                violation_error_message="Já existe um grupo com este nome.",
            )
        ]


class ItemExemplo(OwnedModel):
    descricao = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    grupo = models.ForeignKey(
        GrupoExemplo, null=True, blank=True, on_delete=models.SET_NULL, related_name="itens"
    )

    class Meta:
        ordering = ["id"]
