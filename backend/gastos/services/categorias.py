from gastos.models import Categoria

# Categorias de toda conta nova (US-05; research R-03). Cores = as 7 primeiras da paleta.
CATEGORIAS_PADRAO = (
    ("Moradia", "azul"),
    ("Alimentação", "laranja"),
    ("Transporte", "roxo"),
    ("Saúde", "vermelho"),
    ("Lazer", "rosa"),
    ("Educação", "ciano"),
    ("Outros", "cinza"),
)


def criar_categorias_padrao(usuario):
    """Cria as 7 categorias padrão, só para quem ainda não tem nenhuma (idempotente, FR-001)."""
    if Categoria.objects.do_dono(usuario).exists():
        return
    Categoria.objects.bulk_create(
        Categoria(dono=usuario, nome=nome, cor=cor) for nome, cor in CATEGORIAS_PADRAO
    )
