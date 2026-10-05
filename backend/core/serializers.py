from rest_framework import serializers

MENSAGEM_REGISTRO_NAO_ENCONTRADO = "Registro não encontrado."


class RegistroComDonoSerializer(serializers.ModelSerializer):
    """Base dos serializers de registros com dono (specs/004-isolamento-usuario, R-03).

    O ``dono`` vem sempre da sessão: o valor enviado no payload é ignorado e o campo não aparece
    nas respostas. A subclasse inclui ``"dono"`` em ``Meta.fields``, para que a unicidade por
    dono (``UniqueConstraint(fields=["dono", ...])``) seja validada pelo DRF, que usa a
    ``violation_error_message`` da constraint.
    """

    dono = serializers.HiddenField(default=serializers.CurrentUserDefault())


class RelacionadoDoDonoField(serializers.PrimaryKeyRelatedField):
    """Referência que só aceita registros do usuário da sessão (FR-006; R-04).

    Registro de outra conta e registro inexistente recebem a mesma mensagem.
    """

    default_error_messages = {
        "does_not_exist": MENSAGEM_REGISTRO_NAO_ENCONTRADO,
        "incorrect_type": MENSAGEM_REGISTRO_NAO_ENCONTRADO,
    }

    def get_queryset(self):
        return super().get_queryset().do_dono(self.context["request"].user)
