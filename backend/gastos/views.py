from contextlib import contextmanager

from django.db import IntegrityError, transaction
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.mixins import FiltroPorDonoMixin
from gastos.cores import PALETA
from gastos.models import FORMAS_PAGAMENTO, Categoria, Gasto, MesReferencia
from gastos.serializers import (
    MENSAGEM_MES_REPETIDO,
    MENSAGEM_NOME_REPETIDO,
    CategoriaSerializer,
    GastoSerializer,
    MesReferenciaSerializer,
    TotaisDoMesSerializer,
)
from gastos.services.gastos import (
    RegraViolada,
    excluir_categoria,
    exigir_mes_aberto,
    totais_do_mes,
    verificar_exclusao_do_mes,
)


def salvar_ou_erro_de_unicidade(salvar, erro):
    """Roda ``salvar()`` e converte a violação de unicidade do banco em erro 400 (research R-07).

    Dois envios iguais ao mesmo tempo passam pela validação do serializer; a constraint do banco
    segura o segundo, que vira ``erro`` em vez de erro 500. O ``atomic`` mantém a transação
    utilizável depois do ``IntegrityError``.
    """
    try:
        with transaction.atomic():
            salvar()
    except IntegrityError as excecao:
        raise ValidationError(erro) from excecao


@contextmanager
def regras_como_erro_400():
    """Traduz ``RegraViolada`` do service em ``400 {"detail": "<mensagem>"}`` (research R-03)."""
    try:
        yield
    except RegraViolada as regra:
        raise ValidationError({"detail": str(regra)}) from regra


class CategoriaViewSet(FiltroPorDonoMixin, ModelViewSet):
    """Categorias da pessoa conectada (specs/006-categorias-gasto/contracts/api-categorias.md)."""

    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

    # Nome repetido em envios simultâneos vira o mesmo erro de campo (spec 006, research R-06).
    ERRO_NOME_REPETIDO = {"nome": [MENSAGEM_NOME_REPETIDO]}

    def perform_create(self, serializer):
        salvar_ou_erro_de_unicidade(
            lambda: super(CategoriaViewSet, self).perform_create(serializer), self.ERRO_NOME_REPETIDO
        )

    def perform_update(self, serializer):
        salvar_ou_erro_de_unicidade(
            lambda: super(CategoriaViewSet, self).perform_update(serializer), self.ERRO_NOME_REPETIDO
        )

    DESTINO_INVALIDO = {"mover_para": ["Escolha outra categoria sua para receber os gastos."]}

    def perform_destroy(self, instance):
        # ?mover_para=<id>: categoria que recebe os gastos da excluída (spec 008, research R-07).
        with regras_como_erro_400():
            excluir_categoria(instance, self._destino(instance))

    def _destino(self, categoria):
        valor = self.request.query_params.get("mover_para")
        if valor is None:
            return None
        destino = (
            self.get_queryset().exclude(pk=categoria.pk).filter(pk=valor).first()
            if valor.isdigit()
            else None
        )
        if destino is None:
            raise ValidationError(self.DESTINO_INVALIDO)
        return destino

    @action(detail=False)
    def cores(self, request):
        """Paleta de cores aceitas, na ordem de exibição (FR-013; contracts/api-categorias.md)."""
        return Response([{"codigo": c.codigo, "nome": c.nome, "hex": c.hex} for c in PALETA])


class MesReferenciaViewSet(FiltroPorDonoMixin, ModelViewSet):
    """Meses de referência da pessoa conectada (specs/007-mes-referencia/contracts/api-meses.md)."""

    queryset = MesReferencia.objects.all()
    serializer_class = MesReferenciaSerializer

    # Mês repetido em envios simultâneos vira o mesmo erro do validador (research R-03).
    ERRO_MES_REPETIDO = {"non_field_errors": [MENSAGEM_MES_REPETIDO]}

    def perform_create(self, serializer):
        salvar_ou_erro_de_unicidade(
            lambda: super(MesReferenciaViewSet, self).perform_create(serializer),
            self.ERRO_MES_REPETIDO,
        )

    def perform_update(self, serializer):
        salvar_ou_erro_de_unicidade(
            lambda: super(MesReferenciaViewSet, self).perform_update(serializer),
            self.ERRO_MES_REPETIDO,
        )

    @action(detail=True)
    def totais(self, request, pk=None):
        """Total do mês e por categoria (specs/008-lancar-gastos/contracts/api-gastos.md)."""
        return Response(TotaisDoMesSerializer(totais_do_mes(self.get_object())).data)

    def perform_destroy(self, instance):
        # Mês fechado e mês com gastos não se excluem (spec 007 FR-005; spec 008 FR-009).
        with regras_como_erro_400():
            verificar_exclusao_do_mes(instance)
        super().perform_destroy(instance)


class GastoViewSet(FiltroPorDonoMixin, ModelViewSet):
    """Gastos da pessoa conectada (specs/008-lancar-gastos/contracts/api-gastos.md)."""

    queryset = Gasto.objects.select_related("mes", "categoria")
    serializer_class = GastoSerializer

    # Filtros da lista, aplicados depois do filtro por dono (research R-05).
    FILTROS = {"mes": "Informe o número do mês.", "categoria": "Informe o número da categoria."}

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        for campo, mensagem in self.FILTROS.items():
            valor = self.request.query_params.get(campo)
            if valor is None:
                continue
            if not valor.isdigit():
                raise ValidationError({campo: [mensagem]})
            queryset = queryset.filter(**{f"{campo}_id": int(valor)})
        return queryset

    def perform_create(self, serializer):
        with regras_como_erro_400():
            exigir_mes_aberto(serializer.validated_data["mes"])
        super().perform_create(serializer)

    def perform_update(self, serializer):
        # Vale para o mês de origem e para o de destino, ao mover o gasto (FR-008).
        with regras_como_erro_400():
            exigir_mes_aberto(serializer.instance.mes, serializer.validated_data.get("mes"))
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        with regras_como_erro_400():
            exigir_mes_aberto(instance.mes)
        super().perform_destroy(instance)

    @action(detail=False, url_path="formas-pagamento")
    def formas_pagamento(self, request):
        """Formas de pagamento aceitas, na ordem de exibição (research R-08)."""
        return Response([{"codigo": codigo, "nome": nome} for codigo, nome in FORMAS_PAGAMENTO])
