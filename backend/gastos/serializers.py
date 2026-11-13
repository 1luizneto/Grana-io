import re
from datetime import date
from decimal import Decimal

from rest_framework import serializers

from core.serializers import RegistroComDonoSerializer, RelacionadoDoDonoField
from gastos.cores import CHOICES
from gastos.models import FORMAS_PAGAMENTO, Categoria, Gasto, GastoFixo, MesReferencia
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


class ValorField(serializers.DecimalField):
    """Valor em reais: maior que zero, até 2 casas e 12 dígitos (research R-02).

    Texto vazio conta como ausente: o ``DecimalField`` do DRF o trataria como número inválido.
    """

    LIMITE = "Informe um valor de até 9999999999.99."

    def __init__(self, **kwargs):
        super().__init__(
            max_digits=12,
            decimal_places=2,
            min_value=Decimal("0.01"),
            error_messages={
                "required": OBRIGATORIO,
                "null": OBRIGATORIO,
                "invalid": "Informe um valor numérico, como 12.50.",
                "min_value": "Informe um valor maior que zero.",
                "max_decimal_places": "Use no máximo 2 casas decimais.",
                "max_digits": self.LIMITE,
                "max_whole_digits": self.LIMITE,
                "max_string_length": self.LIMITE,
            },
            **kwargs,
        )

    def to_internal_value(self, data):
        if isinstance(data, str) and not data.strip():
            self.fail("required")
        return super().to_internal_value(data)


class CamposDeGastoSerializer(RegistroComDonoSerializer):
    """Campos comuns ao gasto (spec 008) e ao gasto fixo (spec 010), com as mesmas mensagens."""

    descricao = serializers.CharField(
        max_length=100, error_messages={"blank": OBRIGATORIO, "null": OBRIGATORIO}
    )
    valor = ValorField()
    forma_pagamento = serializers.ChoiceField(
        choices=FORMAS_PAGAMENTO,
        required=False,
        allow_blank=True,
        allow_null=True,
        error_messages={
            "invalid_choice": "Escolha uma forma de pagamento: dinheiro, débito, crédito ou Pix."
        },
    )
    categoria = RelacionadoDoDonoField(queryset=Categoria.objects.all())

    def validate_forma_pagamento(self, valor):
        # Sem forma de pagamento é "" no banco e na resposta (spec 008, research R-08).
        return valor or ""


class GastoSerializer(CamposDeGastoSerializer):
    """Gasto (specs/008-lancar-gastos/contracts/api-gastos.md).

    A regra de mês fechado envolve dois models e fica no service, chamado pela view (R-04).
    ``repetir`` (só na criação) pede à view que cadastre o gasto como fixo (spec 010, R-04).
    """

    data = serializers.DateField(
        error_messages={
            "invalid": "Informe uma data válida no formato AAAA-MM-DD.",
            "null": OBRIGATORIO,
        }
    )
    mes = RelacionadoDoDonoField(queryset=MesReferencia.objects.all())
    repetir = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Gasto
        fields = [
            "id",
            "descricao",
            "valor",
            "data",
            "forma_pagamento",
            "mes",
            "categoria",
            "fixo",
            "repetir",
            "dono",
        ]
        read_only_fields = ["fixo"]

    def validate(self, attrs):
        # Num PATCH parcial, confere contra o mês e a data atuais (FR-003).
        mes = attrs.get("mes", getattr(self.instance, "mes", None))
        data = attrs.get("data", getattr(self.instance, "data", None))
        if mes is not None and data is not None and (data.year, data.month) != (mes.ano, mes.mes):
            raise serializers.ValidationError(
                {"data": [f"A data precisa estar dentro de {mes.rotulo}."]}
            )
        return attrs


class TotalDaCategoriaSerializer(serializers.Serializer):
    categoria = serializers.IntegerField()
    nome = serializers.CharField()
    cor = serializers.CharField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    quantidade = serializers.IntegerField()


class TotaisDoMesSerializer(serializers.Serializer):
    """Saída de ``GET /api/meses/{id}/totais/``: valores em texto com 2 casas (research R-06)."""

    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    por_categoria = TotalDaCategoriaSerializer(many=True)


class MesAnoField(serializers.Field):
    """Mês como texto ``AAAA-MM`` (o formato do ``<input type="month">``), gravado como o dia 1
    (specs/010-gastos-fixos/research.md, R-02)."""

    default_error_messages = {
        "required": OBRIGATORIO,
        "null": OBRIGATORIO,
        "invalid": "Informe o mês no formato AAAA-MM.",
        "ano": "Informe um ano de 2000 a 2100.",
    }
    FORMATO = re.compile(r"(\d{4})-(\d{2})")

    def to_internal_value(self, data):
        if isinstance(data, str) and not data.strip():
            if self.allow_null:
                return None
            self.fail("required")
        encontrado = self.FORMATO.fullmatch(data) if isinstance(data, str) else None
        if not encontrado or not 1 <= int(encontrado.group(2)) <= 12:
            self.fail("invalid")
        ano, mes = int(encontrado.group(1)), int(encontrado.group(2))
        if not 2000 <= ano <= 2100:
            self.fail("ano")
        return date(ano, mes, 1)

    def to_representation(self, value):
        return f"{value.year:04d}-{value.month:02d}"


class GastoFixoSerializer(CamposDeGastoSerializer):
    """Gasto fixo (specs/010-gastos-fixos/contracts/api-fixos.md)."""

    dia_vencimento = InteiroNaFaixaField(
        min_value=1, max_value=31, mensagem="Informe um dia de 1 a 31."
    )
    inicio = MesAnoField()
    fim = MesAnoField(required=False, allow_null=True)

    class Meta:
        model = GastoFixo
        fields = [
            "id",
            "descricao",
            "valor",
            "categoria",
            "forma_pagamento",
            "dia_vencimento",
            "inicio",
            "fim",
            "ativo",
            "dono",
        ]

    def validate(self, attrs):
        # Num PATCH parcial, compara com o início ou o fim atuais (FR-002).
        inicio = attrs.get("inicio", getattr(self.instance, "inicio", None))
        fim = attrs.get("fim", getattr(self.instance, "fim", None))
        if inicio and fim and fim < inicio:
            raise serializers.ValidationError(
                {"fim": ["O mês de fim precisa ser igual ou posterior ao de início."]}
            )
        return attrs
