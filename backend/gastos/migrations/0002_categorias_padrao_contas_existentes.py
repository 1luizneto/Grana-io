"""Dá as categorias padrão às contas criadas antes da US-05 (FR-002; research R-05).

A lista fica copiada aqui, e não importada de gastos.services: uma migration não pode mudar de
comportamento se o código do app mudar depois.
"""

from django.db import migrations

CATEGORIAS_PADRAO = (
    ("Moradia", "azul"),
    ("Alimentação", "laranja"),
    ("Transporte", "roxo"),
    ("Saúde", "vermelho"),
    ("Lazer", "rosa"),
    ("Educação", "ciano"),
    ("Outros", "cinza"),
)


def criar_padrao_para_contas_sem_categorias(apps, schema_editor):
    Usuario = apps.get_model("accounts", "Usuario")
    Categoria = apps.get_model("gastos", "Categoria")
    com_categoria = Categoria.objects.values("dono_id")
    for usuario in Usuario.objects.exclude(id__in=com_categoria):
        Categoria.objects.bulk_create(
            Categoria(dono=usuario, nome=nome, cor=cor) for nome, cor in CATEGORIAS_PADRAO
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("gastos", "0001_initial"),
    ]

    operations = [
        # A volta não apaga nada: a pessoa pode já ter editado as categorias.
        migrations.RunPython(criar_padrao_para_contas_sem_categorias, migrations.RunPython.noop),
    ]
