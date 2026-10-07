from rest_framework import serializers

from core.serializers import RegistroComDonoSerializer
from gastos.cores import CHOICES
from gastos.models import Categoria
from gastos.services.categorias import escolher_cor_livre

MENSAGEM_NOME_REPETIDO = "Já existe uma categoria com este nome."


class CategoriaSerializer(RegistroComDonoSerializer):
    """Categoria de gasto (specs/006-categorias-gasto/contracts/api-categorias.md).

    O nome é único por pessoa sem diferenciar maiúsculas. O DRF não gera validador para a
    constraint com Lower("nome"), então a checagem fica aqui, no campo (research R-06).
    """

    # trim_whitespace (padrão do DRF) tira os espaços das pontas antes de validar e salvar.
    nome = serializers.CharField(max_length=50, error_messages={"blank": "Este campo é obrigatório."})
    # Opcional: sem cor, a criação usa a primeira cor livre da pessoa (research R-07).
    cor = serializers.ChoiceField(
        choices=CHOICES,
        required=False,
        error_messages={"invalid_choice": "Escolha uma das cores disponíveis."},
    )

    class Meta:
        model = Categoria
        fields = ["id", "nome", "cor", "dono"]

    def validate_nome(self, valor):
        mesmas = Categoria.objects.do_dono(self.context["request"].user).filter(nome__iexact=valor)
        if self.instance is not None:
            mesmas = mesmas.exclude(pk=self.instance.pk)
        if mesmas.exists():
            raise serializers.ValidationError(MENSAGEM_NOME_REPETIDO)
        return valor

    def create(self, validated_data):
        validated_data.setdefault("cor", escolher_cor_livre(validated_data["dono"]))
        return super().create(validated_data)
