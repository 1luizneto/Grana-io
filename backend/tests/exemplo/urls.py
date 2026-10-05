"""Rotas da aplicação + rotas de exemplo; usado só por testes com ``pytest.mark.urls``."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from config.urls import urlpatterns as urls_da_aplicacao
from tests.exemplo.views import ItemExemploViewSet

router = DefaultRouter()
router.register("itens", ItemExemploViewSet, basename="exemplo-item")

urlpatterns = [*urls_da_aplicacao, path("api/exemplo/", include(router.urls))]
