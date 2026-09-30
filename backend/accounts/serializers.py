from rest_framework import serializers

from accounts.models import Usuario

MENSAGEM_EMAIL_DUPLICADO = "Já existe uma conta com este e-mail."


class CadastroSerializer(serializers.Serializer):
    """Entrada do cadastro (contracts/api-cadastro.md)."""

    nome = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    senha = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)
    confirmacao_senha = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, valor):
        email = Usuario.normalizar_email(valor)
        # Checagem antecipada para devolver a mensagem junto com os demais erros; a garantia
        # contra cadastros simultâneos é a restrição única do banco (research R-03).
        if Usuario.objects.filter(email=email).exists():
            raise serializers.ValidationError(MENSAGEM_EMAIL_DUPLICADO)
        return email


class UsuarioCadastradoSerializer(serializers.ModelSerializer):
    """Saída do cadastro: só nome e e-mail, sem id nem credenciais (FR-009)."""

    class Meta:
        model = Usuario
        fields = ["nome", "email"]
