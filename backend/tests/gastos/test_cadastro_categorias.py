"""Cadastro cria as categorias padrão na mesma transação (FR-001; research R-04)."""

import pytest

from accounts.models import Usuario
from accounts.services.cadastro import EmailJaCadastrado, cadastrar_usuario
from gastos.models import Categoria

pytestmark = pytest.mark.django_db

SENHA = "uma-senha-boa-2026"
DADOS = {
    "nome": "Ana Souza",
    "email": "ana@exemplo.com",
    "senha": SENHA,
    "confirmacao_senha": SENHA,
}


def test_conta_nova_nasce_com_as_7_categorias(cliente):
    resposta = cliente.post("/api/usuarios/", DADOS, format="json")

    assert resposta.status_code == 201
    usuario = Usuario.objects.get(email="ana@exemplo.com")
    assert Categoria.objects.do_dono(usuario).count() == 7


def test_falha_nas_categorias_desfaz_o_cadastro(monkeypatch):
    def falha(usuario):
        raise RuntimeError("falha ao criar as categorias")

    monkeypatch.setattr("accounts.services.cadastro.criar_categorias_padrao", falha)

    # O erro sobe como é: não vira "e-mail já cadastrado".
    with pytest.raises(RuntimeError):
        cadastrar_usuario(nome="Ana", email="ana@exemplo.com", senha=SENHA)

    assert not Usuario.objects.exists()
    assert not Categoria.objects.exists()


def test_email_duplicado_continua_recusado_sem_criar_nada(cliente):
    cliente.post("/api/usuarios/", DADOS, format="json")

    resposta = cliente.post("/api/usuarios/", DADOS, format="json")

    assert resposta.status_code == 400
    assert resposta.json() == {"email": ["Já existe uma conta com este e-mail."]}
    assert Usuario.objects.count() == 1
    assert Categoria.objects.count() == 7


def test_corrida_de_email_continua_virando_email_ja_cadastrado():
    cadastrar_usuario(nome="Ana", email="ana@exemplo.com", senha=SENHA)

    # Pula a checagem antecipada do serializer: só a restrição do banco segura.
    with pytest.raises(EmailJaCadastrado):
        cadastrar_usuario(nome="Ana 2", email="ana@exemplo.com", senha=SENHA)

    assert Usuario.objects.count() == 1
    assert Categoria.objects.count() == 7
