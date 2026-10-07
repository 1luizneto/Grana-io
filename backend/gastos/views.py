from django.db import IntegrityError, transaction
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.mixins import FiltroPorDonoMixin
from gastos.cores import PALETA
from gastos.models import Categoria, MesReferencia
from gastos.serializers import (
    MENSAGEM_MES_REPETIDO,
    MENSAGEM_NOME_REPETIDO,
    CategoriaSerializer,
    MesReferenciaSerializer,
)


def salvar_ou_erro_de_unicidade(salvar, erro):
    """Roda ``salvar()`` e converte a violação de unicidade do banco em erro 400 (research R-07).

    Dois envios iguais ao mesmo tempo passam pela validação do serializer; a constraint do banco
    segura o segundo, que vira ``erro`` em vez de erro 500. O ``atomic`` mantém a transação
    utilizável depois do ``IntegrityError``.
    """
    try:
        with transaction.atomic():
            salvar()
    except IntegrityError as excecao:
        raise ValidationError(erro) from excecao


class CategoriaViewSet(FiltroPorDonoMixin, ModelViewSet):
    """Categorias da pessoa conectada (specs/006-categorias-gasto/contracts/api-categorias.md)."""

    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

    # Nome repetido em envios simultâneos vira o mesmo erro de campo (spec 006, research R-06).
    ERRO_NOME_REPETIDO = {"nome": [MENSAGEM_NOME_REPETIDO]}

    def perform_create(self, serializer):
        salvar_ou_erro_de_unicidade(
            lambda: super(CategoriaViewSet, self).perform_create(serializer), self.ERRO_NOME_REPETIDO
        )

    def perform_update(self, serializer):
        salvar_ou_erro_de_unicidade(
            lambda: super(CategoriaViewSet, self).perform_update(serializer), self.ERRO_NOME_REPETIDO
        )

    @action(detail=False)
    def cores(self, request):
        """Paleta de cores aceitas, na ordem de exibição (FR-013; contracts/api-categorias.md)."""
        return Response([{"codigo": c.codigo, "nome": c.nome, "hex": c.hex} for c in PALETA])


class MesReferenciaViewSet(FiltroPorDonoMixin, ModelViewSet):
    """Meses de referência da pessoa conectada (specs/007-mes-referencia/contracts/api-meses.md)."""

    queryset = MesReferencia.objects.all()
    serializer_class = MesReferenciaSerializer

    # Mês repetido em envios simultâneos vira o mesmo erro do validador (research R-03).
    ERRO_MES_REPETIDO = {"non_field_errors": [MENSAGEM_MES_REPETIDO]}

    def perform_create(self, serializer):
        salvar_ou_erro_de_unicidade(
            lambda: super(MesReferenciaViewSet, self).perform_create(serializer),
            self.ERRO_MES_REPETIDO,
        )

    def perform_update(self, serializer):
        salvar_ou_erro_de_unicidade(
            lambda: super(MesReferenciaViewSet, self).perform_update(serializer),
            self.ERRO_MES_REPETIDO,
        )
