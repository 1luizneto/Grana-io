"""Kit de testes de isolamento por dono (specs/004-isolamento-usuario, research R-08).

Todo endpoint de dados financeiros declara uma subclasse de ``CasosDeIsolamento`` e herda os
casos mínimos da FR-011 (contracts/isolamento.md, "Testes obrigatórios por recurso"):

    class TestIsolamentoCategoria(CasosDeIsolamento):
        url_lista = "/api/categorias/"
        payload_criacao = {"nome": "Mercado"}
        payload_alteracao = {"nome": "Feira"}

        def criar(self, usuario):
            return Categoria.objects.create(dono=usuario, nome="Mercado")

O módulo da subclasse precisa do marcador ``pytest.mark.django_db``. Ana é ``usuario``
(``cliente_autenticado``) e Bia é ``outro_usuario`` (``cliente_da_bia``), de ``tests/conftest.py``.
"""


class CasosDeIsolamento:
    """Base sem prefixo ``Test``: o pytest só coleta as subclasses."""

    url_lista: str
    payload_criacao: dict
    payload_alteracao: dict

    def url_detalhe(self, pk):
        return f"{self.url_lista}{pk}/"

    def criar(self, usuario):
        """Cria e devolve um registro que pertence a ``usuario``."""
        raise NotImplementedError

    # Listas (US1; FR-004)

    def test_lista_so_do_dono(self, usuario, outro_usuario, cliente_autenticado):
        da_ana = {self.criar(usuario).pk, self.criar(usuario).pk}
        self.criar(outro_usuario)

        resposta = cliente_autenticado.get(self.url_lista)

        assert resposta.status_code == 200
        assert {registro["id"] for registro in resposta.json()} == da_ana

    def test_lista_vazia_sem_pistas(self, outro_usuario, cliente_autenticado):
        self.criar(outro_usuario)

        resposta = cliente_autenticado.get(self.url_lista)

        assert resposta.status_code == 200
        assert resposta.json() == []

    # Registro de outra conta = inexistente (US2; FR-005)

    def _inexistente(self, cliente, metodo, registro, **kwargs):
        return getattr(cliente, metodo)(self.url_detalhe(registro.pk + 1000), **kwargs)

    def _campos(self, registro):
        registro.refresh_from_db()
        return {campo.attname: getattr(registro, campo.attname) for campo in registro._meta.fields}

    def test_abrir_de_outra_conta_igual_a_inexistente(self, outro_usuario, cliente_autenticado):
        da_bia = self.criar(outro_usuario)

        resposta = cliente_autenticado.get(self.url_detalhe(da_bia.pk))
        inexistente = self._inexistente(cliente_autenticado, "get", da_bia)

        assert resposta.status_code == inexistente.status_code == 404
        assert resposta.json() == inexistente.json()

    def test_alterar_de_outra_conta_nao_muda_nada(self, outro_usuario, cliente_autenticado):
        da_bia = self.criar(outro_usuario)
        antes = self._campos(da_bia)

        resposta = cliente_autenticado.patch(
            self.url_detalhe(da_bia.pk), self.payload_alteracao, format="json"
        )
        inexistente = self._inexistente(
            cliente_autenticado, "patch", da_bia, data=self.payload_alteracao, format="json"
        )

        assert resposta.status_code == inexistente.status_code == 404
        assert resposta.json() == inexistente.json()
        assert self._campos(da_bia) == antes

    def test_excluir_de_outra_conta_nao_exclui(self, outro_usuario, cliente_autenticado):
        da_bia = self.criar(outro_usuario)

        resposta = cliente_autenticado.delete(self.url_detalhe(da_bia.pk))
        inexistente = self._inexistente(cliente_autenticado, "delete", da_bia)

        assert resposta.status_code == inexistente.status_code == 404
        assert resposta.json() == inexistente.json()
        assert type(da_bia).objects.filter(pk=da_bia.pk).exists()

    def test_dono_opera_normalmente(self, usuario, cliente_autenticado):
        da_ana = self.criar(usuario)
        url = self.url_detalhe(da_ana.pk)

        assert cliente_autenticado.get(url).status_code == 200
        assert cliente_autenticado.patch(url, self.payload_alteracao, format="json").status_code == 200
        assert cliente_autenticado.delete(url).status_code == 204
        # Registro excluído também é "não encontrado" para o próprio dono (Edge Cases).
        assert cliente_autenticado.get(url).status_code == 404
