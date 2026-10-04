from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from accounts.models import Usuario

MENSAGEM_EMAIL_DUPLICADO = "Já existe uma conta com este e-mail."
MENSAGEM_SENHAS_DIFERENTES = "As senhas não conferem."


class CadastroSerializer(serializers.Serializer):
    """Entrada do cadastro (contracts/api-cadastro.md).

    Todas as regras ficam no nível de campo: o DRF não executa validate() quando algum campo
    tem erro, e as mensagens de senha sumiriam da resposta (FR-008; research R-10).
    """

    nome = serializers.CharField(max_length=150, error_messages={"blank": "Este campo é obrigatório."})
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

    def validate_senha(self, valor):
        # Usuário não salvo, só para o validador de semelhança com nome e e-mail.
        dados = self.initial_data
        usuario = Usuario(
            nome=str(dados.get("nome", "")).strip(),
            email=Usuario.normalizar_email(str(dados.get("email", ""))),
        )
        try:
            validate_password(valor, user=usuario)
        except DjangoValidationError as erro:
            raise serializers.ValidationError(list(erro.messages)) from erro
        return valor

    def validate_confirmacao_senha(self, valor):
        if valor != self.initial_data.get("senha"):
            raise serializers.ValidationError(MENSAGEM_SENHAS_DIFERENTES)
        return valor


class UsuarioSerializer(serializers.ModelSerializer):
    """Dados públicos da conta: só nome e e-mail, sem id nem credenciais."""

    class Meta:
        model = Usuario
        fields = ["nome", "email"]


class EntrarSerializer(serializers.Serializer):
    """Entrada do login (specs/003-login-logout/contracts/api-sessao.md)."""

    email = serializers.CharField()
    senha = serializers.CharField(trim_whitespace=False)


class RenovacaoSerializer(serializers.Serializer):
    """Credencial de renovação enviada para renovar ou encerrar a sessão."""

    renovacao = serializers.CharField()
