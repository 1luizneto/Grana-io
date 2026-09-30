from django.urls import path

from core.views import SaudeView

urlpatterns = [
    path("health/", SaudeView.as_view(), name="saude"),
]
