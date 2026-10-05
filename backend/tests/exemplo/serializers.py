from core.serializers import RegistroComDonoSerializer, RelacionadoDoDonoField
from tests.exemplo.models import GrupoExemplo, ItemExemplo


class GrupoExemploSerializer(RegistroComDonoSerializer):
    class Meta:
        model = GrupoExemplo
        fields = ["id", "nome", "dono"]


class ItemExemploSerializer(RegistroComDonoSerializer):
    grupo = RelacionadoDoDonoField(
        queryset=GrupoExemplo.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = ItemExemplo
        fields = ["id", "descricao", "valor", "grupo", "dono"]
