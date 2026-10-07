"""Migration de dados: contas antigas recebem as categorias padrão (FR-002; research R-05)."""

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

ANTES = [("gastos", "0001_initial")]
DEPOIS = [("gastos", "0002_categorias_padrao_contas_existentes")]


def _migrar(alvo):
    executor = MigrationExecutor(connection)
    executor.migrate(alvo)
    return executor.loader.project_state(alvo).apps


@pytest.mark.django_db(transaction=True)
def test_contas_sem_categorias_recebem_as_padrao_uma_unica_vez():
    try:
        apps = _migrar(ANTES)
        Usuario = apps.get_model("accounts", "Usuario")
        Categoria = apps.get_model("gastos", "Categoria")
        sem = Usuario.objects.create(email="sem@exemplo.com", nome="Sem Categorias", password="x")
        com = Usuario.objects.create(email="com@exemplo.com", nome="Com Categoria", password="x")
        Categoria.objects.create(dono=com, nome="Pets", cor="verde")

        apps = _migrar(DEPOIS)
        Categoria = apps.get_model("gastos", "Categoria")

        assert set(Categoria.objects.filter(dono_id=sem.id).values_list("nome", "cor")) == {
            ("Moradia", "azul"),
            ("Alimentação", "laranja"),
            ("Transporte", "roxo"),
            ("Saúde", "vermelho"),
            ("Lazer", "rosa"),
            ("Educação", "ciano"),
            ("Outros", "cinza"),
        }
        assert list(Categoria.objects.filter(dono_id=com.id).values_list("nome", flat=True)) == ["Pets"]
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
