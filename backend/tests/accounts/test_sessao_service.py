from datetime import timedelta

import pytest
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from accounts.services.sessao import (
    SessaoInvalida,
    autenticar,
    emitir_sessao,
    encerrar_sessao,
    renovar_sessao,
)
from tests.conftest import SENHA

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


# --- Renovação (US4) ---------------------------------------------------------------------


def test_renovar_sessao_devolve_par_novo_e_bloqueia_o_antigo(usuario):
    antiga = emitir_sessao(usuario)["renovacao"]

    nova = renovar_sessao(antiga)

    assert set(nova) == {"acesso", "renovacao"}
    assert nova["renovacao"] != antiga
    assert BlacklistedToken.objects.filter(token__jti=RefreshToken(antiga, verify=False)["jti"]).exists()


def test_renovacao_ja_usada_e_recusada(usuario):
    antiga = emitir_sessao(usuario)["renovacao"]
    renovar_sessao(antiga)

    with pytest.raises(SessaoInvalida):
        renovar_sessao(antiga)


def test_renovacao_vencida_adulterada_ou_de_conta_desativada_e_recusada(usuario):
    vencida = RefreshToken.for_user(usuario)
    vencida.set_exp(lifetime=-timedelta(seconds=1))
    valida = emitir_sessao(usuario)["renovacao"]
    usuario.is_active = False
    usuario.save()

    for renovacao in (str(vencida), "abc.def.ghi", valida):
        with pytest.raises(SessaoInvalida):
            renovar_sessao(renovacao)


# --- Saída (US5) ---------------------------------------------------------------------------


def test_encerrar_sessao_bloqueia_a_renovacao(usuario):
    renovacao = emitir_sessao(usuario)["renovacao"]

    encerrar_sessao(usuario, renovacao)

    with pytest.raises(SessaoInvalida):
        renovar_sessao(renovacao)


def test_encerrar_sessao_de_outra_pessoa_e_recusado_sem_bloquear(usuario, outro_usuario):
    renovacao_da_ana = emitir_sessao(usuario)["renovacao"]

    with pytest.raises(SessaoInvalida):
        encerrar_sessao(outro_usuario, renovacao_da_ana)

    assert BlacklistedToken.objects.count() == 0
    assert renovar_sessao(renovacao_da_ana)["renovacao"]


def test_encerrar_sessao_invalida_e_recusado(usuario):
    ja_encerrada = emitir_sessao(usuario)["renovacao"]
    encerrar_sessao(usuario, ja_encerrada)
    vencida = RefreshToken.for_user(usuario)
    vencida.set_exp(lifetime=-timedelta(seconds=1))

    for renovacao in (ja_encerrada, str(vencida), "abc.def.ghi"):
        with pytest.raises(SessaoInvalida):
            encerrar_sessao(usuario, renovacao)
