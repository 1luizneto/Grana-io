from decimal import Decimal

from django.db.models import Sum
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.mixins import FiltroPorDonoMixin
from tests.exemplo.models import ItemExemplo
from tests.exemplo.serializers import ItemExemploSerializer


class BuscaFilter(SearchFilter):
    search_param = "busca"


class ItemExemploViewSet(FiltroPorDonoMixin, ModelViewSet):
    queryset = ItemExemplo.objects.all()
    serializer_class = ItemExemploSerializer
    filter_backends = [BuscaFilter]
    search_fields = ["descricao"]

    @action(detail=False)
    def total(self, request):
        itens = self.filter_queryset(self.get_queryset())
        soma = itens.aggregate(soma=Sum("valor"))["soma"] or Decimal("0")
        return Response({"quantidade": itens.count(), "soma": f"{soma:.2f}"})
