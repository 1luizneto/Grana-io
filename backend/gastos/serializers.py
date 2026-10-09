from rest_framework import serializers

from core.serializers import RegistroComDonoSerializer
from gastos.cores import CHOICES
from gastos.models import Categoria, MesReferencia
from gastos.services.categorias import escolher_cor_livre

MENSAGEM_NOME_REPETIDO = "Já existe uma categoria com este nome."
MENSAGEM_MES_REPETIDO = "Este mês já foi criado."
OBRIGATORIO = "Este campo é obrigatório."
MENSAGEM_MES_IMUTAVEL = "Não é possível alterar o mês ou o ano. Exclua o mês e crie de novo."


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


class InteiroNaFaixaField(serializers.IntegerField):
    """Inteiro com uma única mensagem para "fora da faixa" e "não é número" (research R-04).

    Texto vazio conta como ausente: o ``IntegerField`` do DRF o trataria como número inválido.
    """

    def __init__(self, *, mensagem, **kwargs):
        mensagens = {"invalid": mensagem, "min_value": mensagem, "max_value": mensagem}
        mensagens.update(required=OBRIGATORIO, null=OBRIGATORIO)
        super().__init__(error_messages=mensagens, **kwargs)

    def to_internal_value(self, data):
        if isinstance(data, str) and not data.strip():
            self.fail("required")
        return super().to_internal_value(data)


class MesReferenciaSerializer(RegistroComDonoSerializer):
    """Mês de referência (specs/007-mes-referencia/contracts/api-meses.md).

    Mês repetido na conta é recusado pelo validador que o DRF gera a partir da
    ``UniqueConstraint(fields=["dono", "ano", "mes"])``, com a mensagem dela (research R-03).
    """

    mes = InteiroNaFaixaField(min_value=1, max_value=12, mensagem="Informe um mês de 1 a 12.")
    ano = InteiroNaFaixaField(
        min_value=2000, max_value=2100, mensagem="Informe um ano de 2000 a 2100."
    )
    rotulo = serializers.CharField(read_only=True)

    class Meta:
        model = MesReferencia
        fields = ["id", "mes", "ano", "rotulo", "fechado", "dono"]

    # Mês e ano só na criação (FR-006). O mesmo valor é aceito, para um PUT completo não falhar.
    def validate_mes(self, valor):
        return self._sem_alterar("mes", valor)

    def validate_ano(self, valor):
        return self._sem_alterar("ano", valor)

    def _sem_alterar(self, campo, valor):
        if self.instance is not None and valor != getattr(self.instance, campo):
            raise serializers.ValidationError(MENSAGEM_MES_IMUTAVEL)
        return valor

    def create(self, validated_data):
        # Todo mês nasce aberto (FR-001); "fechado" enviado na criação é ignorado.
        validated_data["fechado"] = False
        return super().create(validated_data)
