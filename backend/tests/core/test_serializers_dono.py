"""Serializers base de registros com dono (FR-002, FR-003, FR-006; research R-03, R-04)."""

import pytest
from rest_framework import serializers
from rest_framework.test import APIRequestFactory

from core.serializers import RegistroComDonoSerializer, RelacionadoDoDonoField
from tests.exemplo.models import GrupoExemplo, ItemExemplo

pytestmark = pytest.mark.django_db


class ItemSerializer(RegistroComDonoSerializer):
    grupo = RelacionadoDoDonoField(
        queryset=GrupoExemplo.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = ItemExemplo
        fields = ["id", "descricao", "valor", "grupo", "dono"]


def _contexto(usuario):
    request = APIRequestFactory().post("/")
    request.user = usuario
    return {"request": request}


def test_dono_e_oculto_e_vem_da_sessao(usuario, outro_usuario):
    serializer = ItemSerializer(
        data={"descricao": "Mercado", "valor": "10.00", "dono": outro_usuario.pk},
        context=_contexto(usuario),
    )

    assert isinstance(serializer.fields["dono"], serializers.HiddenField)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["dono"] == usuario
    assert "dono" not in serializer.data


def test_referencia_ao_proprio_registro_e_aceita(usuario):
    grupo = GrupoExemplo.objects.create(dono=usuario, nome="Casa")
    serializer = ItemSerializer(
        data={"descricao": "Luz", "valor": "80.00", "grupo": grupo.pk},
        context=_contexto(usuario),
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["grupo"] == grupo


def test_referencia_de_outra_conta_igual_a_inexistente(usuario, outro_usuario):
    da_bia = GrupoExemplo.objects.create(dono=outro_usuario, nome="Casa")

    de_outra_conta = ItemSerializer(
        data={"descricao": "Luz", "valor": "80.00", "grupo": da_bia.pk},
        context=_contexto(usuario),
    )
    inexistente = ItemSerializer(
        data={"descricao": "Luz", "valor": "80.00", "grupo": da_bia.pk + 1000},
        context=_contexto(usuario),
    )

    assert not de_outra_conta.is_valid()
    assert not inexistente.is_valid()
    assert de_outra_conta.errors == inexistente.errors == {"grupo": ["Registro não encontrado."]}
