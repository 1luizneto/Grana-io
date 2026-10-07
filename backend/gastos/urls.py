from rest_framework.routers import SimpleRouter

from gastos.views import CategoriaViewSet, MesReferenciaViewSet

# SimpleRouter: sem a página raiz do DefaultRouter, que listaria as rotas em /api/ (README).
router = SimpleRouter(trailing_slash=True)
router.register("categorias", CategoriaViewSet, basename="categoria")
router.register("meses", MesReferenciaViewSet, basename="mes")

urlpatterns = router.urls
