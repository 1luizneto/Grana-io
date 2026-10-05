from django.conf import settings
from django.db import models


class RegistroDoDonoQuerySet(models.QuerySet):
    def do_dono(self, usuario):
        """Ponto único do filtro por dono: API (mixin), referências e services usam este método."""
        return self.filter(dono=usuario)


class OwnedModel(models.Model):
    """Base de todo registro de dados financeiros (constituição, Princípio II).

    O dono é definido pelo servidor a partir da sessão e nunca muda; registros de outra conta
    são tratados como inexistentes (specs/004-isolamento-usuario/contracts/isolamento.md).
    """

    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
        editable=False,
    )

    objects = RegistroDoDonoQuerySet.as_manager()

    class Meta:
        abstract = True
