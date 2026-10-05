from django.urls import path

from accounts.views import CadastroView, EntrarView, EuView, RenovarView, SairView

urlpatterns = [
    path("usuarios/eu/", EuView.as_view(), name="eu"),
    path("usuarios/", CadastroView.as_view(), name="cadastro"),
    path("auth/entrar/", EntrarView.as_view(), name="entrar"),
    path("auth/renovar/", RenovarView.as_view(), name="renovar"),
    path("auth/sair/", SairView.as_view(), name="sair"),
]
