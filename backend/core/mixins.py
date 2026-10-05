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

    def perform_create(self, serializer):
        serializer.save(dono=self.request.user)
