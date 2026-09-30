import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import CHAVE_DEV_PADRAO, env_bool, env_list, env_str, validar_secret_key

VAR = "GRANA_TESTE_VAR"


@pytest.fixture(autouse=True)
def sem_variavel(monkeypatch):
    monkeypatch.delenv(VAR, raising=False)


class TestEnvStr:
    def test_retorna_valor_definido(self, monkeypatch):
        monkeypatch.setenv(VAR, "valor")
        assert env_str(VAR) == "valor"

    def test_retorna_padrao_quando_ausente(self):
        assert env_str(VAR, "padrao") == "padrao"

    def test_padrao_do_padrao_e_string_vazia(self):
        assert env_str(VAR) == ""


class TestEnvBool:
    @pytest.mark.parametrize("valor", ["1", "true", "TRUE", "True", "yes", "YES", "on", "On"])
    def test_valores_verdadeiros(self, monkeypatch, valor):
        monkeypatch.setenv(VAR, valor)
        assert env_bool(VAR) is True

    @pytest.mark.parametrize("valor", ["0", "false", "no", "off", "", "qualquer"])
    def test_outros_valores_sao_falsos(self, monkeypatch, valor):
        monkeypatch.setenv(VAR, valor)
        assert env_bool(VAR, True) is False

    def test_retorna_padrao_quando_ausente(self):
        assert env_bool(VAR) is False
        assert env_bool(VAR, True) is True


class TestEnvList:
    def test_separa_por_virgula_remove_espacos_e_ignora_vazios(self, monkeypatch):
        monkeypatch.setenv(VAR, "a, ,b,")
        assert env_list(VAR) == ["a", "b"]

    def test_valor_unico(self, monkeypatch):
        monkeypatch.setenv(VAR, "*")
        assert env_list(VAR) == ["*"]

    def test_vazia_retorna_lista_vazia(self, monkeypatch):
        monkeypatch.setenv(VAR, "")
        assert env_list(VAR) == []

    def test_ausente_retorna_lista_vazia(self):
        assert env_list(VAR) == []


class TestValidarSecretKey:
    """FR-012: fora do modo de desenvolvimento a chave padrão é recusada."""

    def test_recusa_chave_padrao_fora_do_modo_dev(self):
        with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
            validar_secret_key(CHAVE_DEV_PADRAO, debug=False)

    def test_recusa_chave_vazia_fora_do_modo_dev(self):
        with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
            validar_secret_key("", debug=False)

    def test_aceita_chave_propria_fora_do_modo_dev(self):
        validar_secret_key("uma-chave-propria-e-longa", debug=False)

    def test_aceita_chave_padrao_no_modo_dev(self):
        validar_secret_key(CHAVE_DEV_PADRAO, debug=True)
