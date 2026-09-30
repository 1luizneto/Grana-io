from django.core.exceptions import ValidationError

# Senhas comuns em português que a lista do CommonPasswordValidator não cobre
# (verificado no Django 5.2.17; specs/002-cadastro-usuario/research.md R-04).
SENHAS_COMUNS_PTBR = frozenset(
    {
        "mudar123",
        "brasil123",
        "corinthians",
        "palmeiras",
        "saopaulo",
        "vasco123",
        "gremio123",
        "cruzeiro",
        "amor1234",
        "familia123",
        "jesus123",
        "deus1234",
        "senhasenha",
        "abcd1234",
        "qwerty123",
    }
)


class SenhaComumPtBrValidator:
    """Complementa o CommonPasswordValidator com senhas comuns em português."""

    def validate(self, password, user=None):
        if password.lower() in SENHAS_COMUNS_PTBR:
            raise ValidationError("Esta senha é muito comum.", code="password_too_common")

    def get_help_text(self):
        return "Sua senha não pode ser uma senha comumente utilizada."
