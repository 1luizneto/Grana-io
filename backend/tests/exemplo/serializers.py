from rest_framework import serializers

from tests.exemplo.models import ItemExemplo


class ItemExemploSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemExemplo
        fields = ["id", "descricao", "valor", "grupo"]
