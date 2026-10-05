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
