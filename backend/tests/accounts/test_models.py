import pytest
from django.contrib.auth import get_user_model

from accounts.models import Usuario

SENHA = "uma-senha-boa-2026"

pytestmark = pytest.mark.django_db


def test_modelo_de_usuario_do_projeto_e_identificado_por_email():
    assert get_user_model() is Usuario
    assert Usuario.USERNAME_FIELD == "email"


def test_create_user_normaliza_email_e_nome():
    usuario = Usuario.objects.create_user(email=" Ana@Exemplo.COM ", nome="  Ana  ", password=SENHA)

    assert usuario.email == "ana@exemplo.com"
    assert usuario.nome == "Ana"


def test_create_user_guarda_senha_so_como_hash():
    usuario = Usuario.objects.create_user(email="ana@exemplo.com", nome="Ana", password=SENHA)

    assert usuario.password.startswith("pbkdf2_sha256$")
    assert SENHA not in usuario.password
    assert usuario.check_password(SENHA)


def test_create_user_cria_conta_ativa_sem_privilegios():
    usuario = Usuario.objects.create_user(email="ana@exemplo.com", nome="Ana", password=SENHA)

    assert usuario.is_active is True
    assert usuario.is_staff is False
    assert usuario.is_superuser is False
    assert usuario.criado_em is not None
    assert str(usuario) == "ana@exemplo.com"


def test_create_superuser_tem_privilegios():
    admin = Usuario.objects.create_superuser(email="admin@exemplo.com", nome="Admin", password=SENHA)

    assert admin.is_staff is True
    assert admin.is_superuser is True


def test_save_normaliza_email():
    usuario = Usuario(email="X@Y.com", nome="X")
    usuario.set_password(SENHA)
    usuario.save()

    usuario.refresh_from_db()
    assert usuario.email == "x@y.com"


def test_get_by_natural_key_ignora_caixa_e_espacos():
    Usuario.objects.create_user(email="ana@exemplo.com", nome="Ana", password=SENHA)

    assert Usuario.objects.get_by_natural_key(" ANA@Exemplo.com ").email == "ana@exemplo.com"
