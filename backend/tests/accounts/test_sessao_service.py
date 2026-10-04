import pytest
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import AccessToken

from accounts.services.sessao import autenticar, emitir_sessao
from tests.accounts.conftest import SENHA

pytestmark = pytest.mark.django_db


def test_autenticar_ignora_caixa_e_espacos_do_email(usuario):
    assert autenticar(email=" ANA@Exemplo.com ", senha=SENHA) == usuario


def test_emitir_sessao_devolve_credenciais_do_usuario(usuario):
    sessao = emitir_sessao(usuario)

    assert set(sessao) == {"acesso", "renovacao"}
    assert sessao["acesso"] and sessao["renovacao"]
    assert str(AccessToken(sessao["acesso"])["user_id"]) == str(usuario.pk)


def test_emitir_sessao_registra_ultimo_acesso_e_renovacao_emitida(usuario):
    assert usuario.last_login is None

    emitir_sessao(usuario)

    usuario.refresh_from_db()
    assert usuario.last_login is not None
    assert OutstandingToken.objects.filter(user=usuario).count() == 1
