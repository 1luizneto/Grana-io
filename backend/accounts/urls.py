from django.urls import path

from accounts.views import CadastroView, EntrarView, EuView

urlpatterns = [
    path("usuarios/eu/", EuView.as_view(), name="eu"),
    path("usuarios/", CadastroView.as_view(), name="cadastro"),
    path("auth/entrar/", EntrarView.as_view(), name="entrar"),
]
