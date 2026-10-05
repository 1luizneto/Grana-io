"""Guardas de isolamento: todo registro novo já nasce isolado (US4; FR-010; research R-06).

Exceções em ``MODELS_SEM_DONO`` só valem para o próprio ``Usuario`` e para dados de referência
compartilhados, somente leitura pela API (constituição v1.2.0, Princípio II). Cada entrada leva
um comentário com a spec que a criou, e o ``plan.md`` dessa spec justifica a exceção.
"""

from pathlib import Path

import pytest
from django.apps import apps
from django.conf import settings
from django.urls import get_resolver

from accounts.models import Usuario
from core.mixins import FiltroPorDonoMixin
from core.models import OwnedModel
from tests.exemplo.models import ItemExemplo
from tests.isolamento import modelos_sem_dono
from tests.rotas import rotas

MODELS_SEM_DONO = {
    "accounts.Usuario",  # é o próprio dono (spec 004)
}


def _models_do_projeto():
    raiz = Path(settings.BASE_DIR).resolve()
    for app in apps.get_app_configs():
        if Path(app.path).resolve().is_relative_to(raiz):
            yield from app.get_models()


def test_funcao_aponta_model_sem_dono():
    assert modelos_sem_dono([Usuario, ItemExemplo], excecoes=set()) == ["accounts.Usuario"]


def test_funcao_respeita_excecoes():
    assert modelos_sem_dono([Usuario, ItemExemplo], excecoes={"accounts.Usuario"}) == []


def test_guarda_todo_model_do_projeto_tem_dono():
    sem_dono = modelos_sem_dono(_models_do_projeto(), excecoes=MODELS_SEM_DONO)

    assert sem_dono == [], (
        f"Models sem dono: {sem_dono}. Todo registro de dados financeiros herda de "
        "core.models.OwnedModel. Exceção só para dados de referência compartilhados, somente "
        "leitura (constituição v1.2.0, Princípio II): declare em MODELS_SEM_DONO com comentário "
        "citando a spec e justifique no plan.md dela."
    )


@pytest.mark.urls("tests.exemplo.urls")
def test_guarda_toda_view_de_registro_com_dono_usa_o_filtro():
    # Um viewset gera várias rotas (lista, detalhe, ações, sufixo de formato): agrupa por view.
    sem_filtro = {}
    for caminho, padrao in rotas(get_resolver().url_patterns):
        view = getattr(padrao.callback, "cls", None) or getattr(padrao.callback, "view_class", None)
        queryset = getattr(view, "queryset", None)
        if queryset is None or not issubclass(queryset.model, OwnedModel):
            continue
        if not issubclass(view, FiltroPorDonoMixin):
            sem_filtro.setdefault(view.__name__, caminho)

    assert sem_filtro == {}, (
        f"Views de registros com dono sem FiltroPorDonoMixin (view: primeira rota): {sem_filtro}. "
        "O mixin vem antes da classe do DRF na herança (contracts/isolamento.md)."
    )
