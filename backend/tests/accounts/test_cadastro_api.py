"""Contrato: specs/002-cadastro-usuario/contracts/api-cadastro.md"""

import pytest
from django.test import RequestFactory, override_settings
from django.views.debug import SafeExceptionReporterFilter
from rest_framework.test import APIClient

from accounts.models import Usuario
from accounts.views import CadastroView

URL = "/api/usuarios/"
SENHA = "uma-senha-boa-2026"

pytestmark = pytest.mark.django_db


def dados(**sobrescritos):
    base = {
        "nome": "Ana Souza",
        "email": "ana@exemplo.com",
        "senha": SENHA,
        "confirmacao_senha": SENHA,
    }
    base.update(sobrescritos)
    return base


@pytest.fixture
def cliente():
    # Sem autenticação: o cadastro é público (FR-001).
    return APIClient()


def test_cadastro_valido_retorna_201_so_com_nome_e_email(cliente):
    resposta = cliente.post(URL, dados(nome="  Ana Souza ", email=" Ana@Exemplo.com "), format="json")

    assert resposta.status_code == 201
    assert resposta.json() == {"nome": "Ana Souza", "email": "ana@exemplo.com"}
    assert SENHA not in resposta.content.decode()


def test_cadastro_cria_conta_ativa_sem_privilegios(cliente):
    cliente.post(URL, dados(), format="json")

    usuario = Usuario.objects.get(email="ana@exemplo.com")
    assert usuario.is_active is True
    assert usuario.is_staff is False
    assert usuario.is_superuser is False


@pytest.mark.parametrize("metodo", ["get", "put", "patch", "delete"])
def test_outros_metodos_nao_permitidos(cliente, metodo):
    assert getattr(cliente, metodo)(URL).status_code == 405


@override_settings(CADASTRO_ABERTO=False)
def test_cadastro_fechado_recusa_mesmo_com_dados_validos(cliente):
    resposta = cliente.post(URL, dados(), format="json")

    assert resposta.status_code == 403
    assert resposta.json() == {"detail": "O cadastro de novas contas está desativado neste sistema."}
    assert Usuario.objects.count() == 0


def test_senha_mascarada_na_pagina_de_erro():
    request = RequestFactory().post(URL, data=dados())

    CadastroView.as_view()(request)

    parametros = SafeExceptionReporterFilter().get_post_parameters(request)
    assert parametros["senha"] == "********************"
    assert parametros["confirmacao_senha"] == "********************"
    assert parametros["nome"] == "Ana Souza"


MENSAGEM_DUPLICADO = {"email": ["Já existe uma conta com este e-mail."]}


@pytest.mark.parametrize("email", ["ana@exemplo.com", "ANA@Exemplo.com", "  ana@exemplo.com  "])
def test_email_ja_cadastrado_e_recusado(cliente, email):
    Usuario.objects.create_user(email="ana@exemplo.com", nome="Ana", password=SENHA)

    resposta = cliente.post(URL, dados(email=email), format="json")

    assert resposta.status_code == 400
    assert resposta.json() == MENSAGEM_DUPLICADO
    assert Usuario.objects.filter(email="ana@exemplo.com").count() == 1


def test_corrida_de_email_duplicado_responde_400_e_nao_500(cliente, monkeypatch):
    # Simula dois cadastros simultâneos: a checagem do serializer passa, mas a restrição do banco
    # recusa o segundo.
    Usuario.objects.create_user(email="ana@exemplo.com", nome="Ana", password=SENHA)
    monkeypatch.setattr(
        "accounts.serializers.CadastroSerializer.validate_email",
        lambda self, valor: Usuario.normalizar_email(valor),
    )

    resposta = cliente.post(URL, dados(), format="json")

    assert resposta.status_code == 400
    assert resposta.json() == MENSAGEM_DUPLICADO
    assert Usuario.objects.filter(email="ana@exemplo.com").count() == 1


OBRIGATORIO = "Este campo é obrigatório."
CASOS_INVALIDOS = {
    "nome_so_espacos": ({"nome": "   "}, {"nome": OBRIGATORIO}),
    "nome_longo": ({"nome": "a" * 151}, {"nome": None}),
    "email_sem_dominio": ({"email": "ana@"}, {"email": "Insira um endereço de email válido."}),
    "email_sem_arroba": ({"email": "ana.exemplo.com"}, {"email": "Insira um endereço de email válido."}),
    "email_longo": ({"email": "a" * 250 + "@x.com"}, {"email": None}),
    "confirmacao_diferente": ({"confirmacao_senha": "outra-senha-boa-9"}, {"confirmacao_senha": "As senhas não conferem."}),
    "senha_curta": ({"senha": "abc12", "confirmacao_senha": "abc12"}, {"senha": "8 caracteres"}),
    "senha_numerica": ({"senha": "98765432109", "confirmacao_senha": "98765432109"}, {"senha": "Esta senha é inteiramente numérica."}),
    "senha_comum": ({"senha": "senha123", "confirmacao_senha": "senha123"}, {"senha": "Esta senha é muito comum."}),
    "senha_comum_ptbr": ({"senha": "mudar123", "confirmacao_senha": "mudar123"}, {"senha": "Esta senha é muito comum."}),
    "senha_parecida": (
        {"nome": "Carlos Mendes", "email": "carlos.mendes@exemplo.com", "senha": "carlosmendes", "confirmacao_senha": "carlosmendes"},
        {"senha": None},
    ),
    "senha_longa": ({"senha": "a1b2" * 32 + "x", "confirmacao_senha": "a1b2" * 32 + "x"}, {"senha": None}),
}


@pytest.mark.parametrize("sobrescritos,esperado", CASOS_INVALIDOS.values(), ids=CASOS_INVALIDOS.keys())
def test_dados_invalidos_sao_recusados_no_campo_certo(cliente, sobrescritos, esperado):
    resposta = cliente.post(URL, dados(**sobrescritos), format="json")

    assert resposta.status_code == 400
    erros = resposta.json()
    for campo, trecho in esperado.items():
        assert campo in erros
        if trecho:
            assert any(trecho in mensagem for mensagem in erros[campo]), erros[campo]
    assert Usuario.objects.count() == 0


def test_campos_ausentes_sao_obrigatorios(cliente):
    resposta = cliente.post(URL, {}, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {
        "nome": [OBRIGATORIO],
        "email": [OBRIGATORIO],
        "senha": [OBRIGATORIO],
        "confirmacao_senha": [OBRIGATORIO],
    }


def test_varios_problemas_voltam_juntos(cliente):
    resposta = cliente.post(
        URL, {"nome": "   ", "email": "ana@", "senha": "123", "confirmacao_senha": "456"}, format="json"
    )

    assert resposta.status_code == 400
    erros = resposta.json()
    assert set(erros) == {"nome", "email", "senha", "confirmacao_senha"}
    assert any("8 caracteres" in m for m in erros["senha"])
    assert "Esta senha é inteiramente numérica." in erros["senha"]
    assert erros["confirmacao_senha"] == ["As senhas não conferem."]
    assert Usuario.objects.count() == 0


def test_senha_com_espacos_e_preservada(cliente):
    senha = "  espaços contam  "
    resposta = cliente.post(URL, dados(senha=senha, confirmacao_senha=senha), format="json")

    assert resposta.status_code == 201
    assert Usuario.objects.get(email="ana@exemplo.com").check_password(senha)


def test_nome_com_acentos_e_apostrofo(cliente):
    resposta = cliente.post(URL, dados(nome="João D'Ávila"), format="json")

    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "João D'Ávila"


def test_campos_em_branco_sao_obrigatorios(cliente):
    # A interface envia os campos vazios, não ausentes (specs/005-telas-login-cadastro, T022).
    resposta = cliente.post(
        URL, {"nome": "", "email": "", "senha": "", "confirmacao_senha": ""}, format="json"
    )

    assert resposta.status_code == 400
    assert resposta.json() == {
        "nome": [OBRIGATORIO],
        "email": [OBRIGATORIO],
        "senha": [OBRIGATORIO],
        "confirmacao_senha": [OBRIGATORIO],
    }
