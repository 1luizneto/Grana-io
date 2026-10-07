from gastos.cores import CODIGOS
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


def escolher_cor_livre(usuario):
    """Primeira cor da paleta que a pessoa ainda não usa; com todas em uso, segue a ordem da
    paleta pela quantidade de categorias (FR-007; research R-07)."""
    categorias = Categoria.objects.do_dono(usuario)
    em_uso = set(categorias.values_list("cor", flat=True))
    for codigo in CODIGOS:
        if codigo not in em_uso:
            return codigo
    return CODIGOS[categorias.count() % len(CODIGOS)]
