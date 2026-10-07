from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from core.mixins import FiltroPorDonoMixin
from gastos.models import Categoria
from gastos.serializers import MENSAGEM_NOME_REPETIDO, CategoriaSerializer


class CategoriaViewSet(FiltroPorDonoMixin, ModelViewSet):
    """Categorias da pessoa conectada (specs/006-categorias-gasto/contracts/api-categorias.md)."""

    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

    # Dois envios simultâneos com o mesmo nome passam pela validação; a constraint do banco segura
    # o segundo, que vira o mesmo erro de campo em vez de erro 500 (research R-06).
    def perform_create(self, serializer):
        self._salvar(lambda: super(CategoriaViewSet, self).perform_create(serializer))

    def perform_update(self, serializer):
        self._salvar(lambda: super(CategoriaViewSet, self).perform_update(serializer))

    @staticmethod
    def _salvar(salvar):
        try:
            with transaction.atomic():
                salvar()
        except IntegrityError as erro:
            raise ValidationError({"nome": [MENSAGEM_NOME_REPETIDO]}) from erro
