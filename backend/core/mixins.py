from django.http import Http404
from rest_framework.exceptions import NotFound


class FiltroPorDonoMixin:
    """Isola as views de registros com dono (specs/004-isolamento-usuario/contracts/isolamento.md).

    Filtra o queryset pelo usuário da sessão antes de busca, filtros, leitura, alteração e
    exclusão; registro de outra conta cai no mesmo 404 de um inexistente. Na criação, o dono é
    sempre quem está conectado.

    Deve vir **antes** da classe do DRF na herança:
    ``class GastoViewSet(FiltroPorDonoMixin, ModelViewSet)``.
    """

    def get_queryset(self):
        return super().get_queryset().do_dono(self.request.user)

    def get_object(self):
        # O DRF repassa o texto do Http404 do Django ("No <Model> matches the given query."), que
        # vem em inglês e revela o nome interno do model. Todo "não encontrado" sai igual.
        try:
            return super().get_object()
        except Http404:
            raise NotFound from None

    def perform_create(self, serializer):
        serializer.save(dono=self.request.user)
