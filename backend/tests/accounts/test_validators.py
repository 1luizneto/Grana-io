import pytest
from django.core.exceptions import ValidationError

from accounts.validators import SenhaComumPtBrValidator


@pytest.mark.parametrize("senha", ["mudar123", "brasil123", "corinthians", "Brasil123"])
def test_recusa_senhas_comuns_em_portugues(senha):
    with pytest.raises(ValidationError) as erro:
        SenhaComumPtBrValidator().validate(senha)

    assert erro.value.messages == ["Esta senha é muito comum."]


def test_aceita_senha_nao_comum():
    SenhaComumPtBrValidator().validate("uma-senha-boa-2026")


def test_texto_de_ajuda_em_portugues():
    assert SenhaComumPtBrValidator().get_help_text() == (
        "Sua senha não pode ser uma senha comumente utilizada."
    )
