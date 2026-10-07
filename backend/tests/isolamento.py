"""Kit de testes de isolamento por dono (specs/004-isolamento-usuario, research R-08).

Todo endpoint de dados financeiros declara uma subclasse de ``CasosDeIsolamento`` e herda os
casos mínimos da FR-011 (contracts/isolamento.md, "Testes obrigatórios por recurso"):

    class TestIsolamentoCategoria(CasosDeIsolamento):
        modelo = Categoria
        url_lista = "/api/categorias/"
        payload_criacao = {"nome": "Mercado"}
        payload_alteracao = {"nome": "Feira"}

        def criar(self, usuario):
            # O kit cria vários registros por conta: gere valores únicos se houver unicidade.
            return Categoria.objects.create(
                dono=usuario, nome=f"Categoria {Categoria.objects.count() + 1}", cor="azul"
            )

O módulo da subclasse precisa do marcador ``pytest.mark.django_db``. Ana é ``usuario``
(``cliente_autenticado``) e Bia é ``outro_usuario`` (``cliente_da_bia``), de ``tests/conftest.py``.
"""

from core.models import OwnedModel


def modelos_sem_dono(models, excecoes):
    """Devolve, ordenados, os ``"<app>.<Model>"`` concretos que não herdam de ``OwnedModel``.

    Usada pela guarda de models (tests/core/test_guarda_isolamento.py; research R-06).
    """
    return sorted(
        model._meta.label
        for model in models
        if not model._meta.abstract
        and not model._meta.proxy
        and not issubclass(model, OwnedModel)
        and model._meta.label not in excecoes
    )


class CasosDeIsolamento:
    """Base sem prefixo ``Test``: o pytest só coleta as subclasses."""

    modelo: type
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
        assert self.modelo.objects.filter(pk=da_bia.pk).exists()

    def test_dono_opera_normalmente(self, usuario, cliente_autenticado):
        da_ana = self.criar(usuario)
        url = self.url_detalhe(da_ana.pk)

        assert cliente_autenticado.get(url).status_code == 200
        assert cliente_autenticado.patch(url, self.payload_alteracao, format="json").status_code == 200
        assert cliente_autenticado.delete(url).status_code == 204
        # Registro excluído também é "não encontrado" para o próprio dono (Edge Cases).
        assert cliente_autenticado.get(url).status_code == 404

    # O dono é sempre quem está conectado (US3; FR-002, FR-003)

    def test_dono_do_payload_ignorado_na_criacao(self, usuario, outro_usuario, cliente_autenticado):
        resposta = cliente_autenticado.post(
            self.url_lista, {**self.payload_criacao, "dono": outro_usuario.pk}, format="json"
        )

        assert resposta.status_code == 201
        assert "dono" not in resposta.json()
        criado = self.modelo.objects.get(pk=resposta.json()["id"])
        assert criado.dono == usuario

    def test_dono_do_payload_ignorado_na_alteracao(
        self, usuario, outro_usuario, cliente_autenticado
    ):
        da_ana = self.criar(usuario)

        resposta = cliente_autenticado.patch(
            self.url_detalhe(da_ana.pk), {"dono": outro_usuario.pk}, format="json"
        )

        assert resposta.status_code == 200
        assert "dono" not in resposta.json()
        da_ana.refresh_from_db()
        assert da_ana.dono == usuario
