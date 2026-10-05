"""Base comum de registro com dono (FR-001, FR-007, FR-012; research R-01)."""

from decimal import Decimal

import pytest
from django.conf import settings
from django.db import IntegrityError, models, transaction

from core.models import OwnedModel
from tests.exemplo.models import GrupoExemplo, ItemExemplo

pytestmark = pytest.mark.django_db


def _item(dono, descricao="Mercado", valor="10.00"):
    return ItemExemplo.objects.create(dono=dono, descricao=descricao, valor=Decimal(valor))


def test_owned_model_e_abstrato():
    assert OwnedModel._meta.abstract is True


def test_campo_dono():
    campo = ItemExemplo._meta.get_field("dono")

    assert campo.related_model._meta.label == settings.AUTH_USER_MODEL
    assert campo.editable is False
    assert campo.remote_field.on_delete is models.CASCADE
    assert campo.remote_field.related_name == "+"
    assert campo.db_index is True


def test_do_dono_devolve_so_os_registros_do_usuario(usuario, outro_usuario):
    da_ana = [_item(usuario), _item(usuario)]
    _item(outro_usuario)

    assert list(ItemExemplo.objects.do_dono(usuario)) == da_ana


def test_registro_sem_dono_e_recusado_pelo_banco():
    with pytest.raises(IntegrityError), transaction.atomic():
        ItemExemplo.objects.create(descricao="Sem dono", valor=Decimal("1.00"))


def test_conta_removida_leva_os_registros_junto(usuario, outro_usuario):
    do_ana = _item(usuario)
    _item(outro_usuario)

    outro_usuario.delete()

    assert list(ItemExemplo.objects.all()) == [do_ana]


def test_nome_unico_vale_dentro_de_cada_conta(usuario, outro_usuario):
    GrupoExemplo.objects.create(dono=usuario, nome="Mercado")
    GrupoExemplo.objects.create(dono=outro_usuario, nome="Mercado")

    with pytest.raises(IntegrityError), transaction.atomic():
        GrupoExemplo.objects.create(dono=usuario, nome="Mercado")

    assert GrupoExemplo.objects.count() == 2
