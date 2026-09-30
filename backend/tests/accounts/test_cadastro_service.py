import pytest
from django.test import override_settings

from accounts.models import Usuario
from accounts.services.cadastro import cadastrar_usuario, cadastro_aberto

SENHA = "uma-senha-boa-2026"

pytestmark = pytest.mark.django_db


def test_cadastrar_usuario_persiste_com_email_normalizado_e_senha_verificavel():
    usuario = cadastrar_usuario(nome="Ana", email="Ana@Exemplo.com", senha=SENHA)

    usuario.refresh_from_db()
    assert usuario.email == "ana@exemplo.com"
    assert usuario.check_password(SENHA)


def test_cadastrar_usuario_e_atomico(monkeypatch):
    original = Usuario.objects.create_user

    def cria_e_falha(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("falha depois de criar o usuário")

    monkeypatch.setattr(Usuario.objects, "create_user", cria_e_falha)

    with pytest.raises(RuntimeError):
        cadastrar_usuario(nome="Ana", email="ana@exemplo.com", senha=SENHA)

    assert Usuario.objects.count() == 0


@pytest.mark.parametrize("aberto", [True, False])
def test_cadastro_aberto_segue_a_configuracao(aberto):
    with override_settings(CADASTRO_ABERTO=aberto):
        assert cadastro_aberto() is aberto


def test_email_ja_gravado_no_banco_lanca_email_ja_cadastrado():
    from accounts.services.cadastro import EmailJaCadastrado

    Usuario.objects.create_user(email="ana@exemplo.com", nome="Ana", password=SENHA)

    with pytest.raises(EmailJaCadastrado):
        cadastrar_usuario(nome="Outra", email="ANA@exemplo.com", senha=SENHA)

    assert Usuario.objects.filter(email="ana@exemplo.com").count() == 1
