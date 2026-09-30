from django.urls import path

from accounts.views import CadastroView

urlpatterns = [
    path("usuarios/", CadastroView.as_view(), name="cadastro"),
]
