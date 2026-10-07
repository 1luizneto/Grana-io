# Research: Categorias de Gasto

**Feature**: `006-categorias-gasto` | **Plano**: [plan.md](plan.md)

Primeiro dado financeiro real. Segue a regra de dono da spec 004 (`OwnedModel`,
`FiltroPorDonoMixin`, `RegistroComDonoSerializer`, kit `CasosDeIsolamento`) e os padrões de tela
da spec 005.

---

## R-01 — App novo `gastos`

**Decisão**: criar o app `backend/gastos/` (épico EP-02), com o model `Categoria` agora. Mês
(US-06), gasto (US-07) e recorrentes (US-07b) entram no mesmo app depois.

**Rationale**: `docs/arquitetura.md` §2.3 cita `gastos` como exemplo de app de domínio. Categoria,
mês e gasto se referenciam e mudam juntos; um app por épico evita dependências cruzadas.

**Alternativas**: app `categorias` só para isso (fragmenta o domínio do EP-02); colocar no `core`
(o `core` é infraestrutura comum, não domínio).

---

## R-02 — Paleta: 12 cores definidas no backend, guardadas por código

**Decisão**: a paleta fica em `gastos/cores.py`, como uma tupla ordenada de
`Cor(codigo, nome, hex)`. A categoria guarda o **código** (ex.: `"verde"`), não o hexadecimal. A
API expõe a paleta em `GET /api/categorias/cores/`, e a interface desenha as amostras com o `hex`
que recebe (FR-013; Princípio V).

| Ordem | Código | Nome | Hex |
|---|---|---|---|
| 1 | `azul` | Azul | `#2563EB` |
| 2 | `laranja` | Laranja | `#EA580C` |
| 3 | `roxo` | Roxo | `#7C3AED` |
| 4 | `vermelho` | Vermelho | `#DC2626` |
| 5 | `rosa` | Rosa | `#DB2777` |
| 6 | `ciano` | Ciano | `#0891B2` |
| 7 | `cinza` | Cinza | `#6B7280` |
| 8 | `verde` | Verde | `#16A34A` |
| 9 | `amarelo` | Amarelo | `#CA8A04` |
| 10 | `marrom` | Marrom | `#92400E` |
| 11 | `oliva` | Oliva | `#65A30D` |
| 12 | `indigo` | Índigo | `#4F46E5` |

Tons de intensidade média (família 600 do Tailwind, sem usar a biblioteca): contraste mínimo de
3:1 contra fundo branco e contra fundo escuro (`#111827`), suficiente para áreas de gráfico, e
distintos entre si.

**Rationale**: guardar o código desacopla o dado da aparência: ajustar um tom (RNF-04, tema
escuro) não exige migrar dados. A validação vira um `ChoiceField`.

**Alternativas**: guardar o hex (trocar um tom exigiria migração); paleta só na interface
(viola o Princípio V: a interface decidiria quais valores são válidos).

---

## R-03 — Categorias padrão e cores

**Decisão**: constante `CATEGORIAS_PADRAO` em `gastos/services/categorias.py`:

| Nome | Cor |
|---|---|
| Moradia | `azul` |
| Alimentação | `laranja` |
| Transporte | `roxo` |
| Saúde | `vermelho` |
| Lazer | `rosa` |
| Educação | `ciano` |
| Outros | `cinza` |

São as 7 primeiras cores da paleta, na mesma ordem, todas diferentes entre si.

---

## R-04 — Criação no cadastro: chamada explícita na mesma transação

**Decisão**: `gastos.services.categorias.criar_categorias_padrao(usuario)` cria as 7 com
`bulk_create`, **só se a pessoa não tiver nenhuma categoria** (idempotente). O
`accounts.services.cadastro.cadastrar_usuario` chama a função logo depois do `create_user`, dentro
do mesmo `transaction.atomic()` (o comentário-gancho da spec 002 já marca o lugar). Se a criação
das categorias falhar, a conta também não é criada.

O `except IntegrityError` do cadastro hoje assume que só o e-mail pode falhar. A chamada fica
**fora** do trecho protegido por esse `except` (um bloco `atomic` externo envolve os dois passos,
e o `try/except` envolve só o `create_user`), para que um erro nas categorias não vire "e-mail já
cadastrado".

**Rationale**: `docs/arquitetura.md` §5 proíbe signals e cita exatamente este caso ("criar
categorias padrão no cadastro") como chamada explícita no service.

**Alternativas**: signal `post_save` (rejeitado pelo documento de arquitetura); criar na primeira
listagem (efeito colateral num GET e corrida entre requisições).

---

## R-05 — Contas antigas: migration de dados

**Decisão**: migration `gastos/migrations/0002_categorias_padrao_contas_existentes.py` com
`RunPython`: para cada usuário sem nenhuma categoria, cria as 7 padrão. A lista de nomes e cores é
**copiada** dentro da migration (migrations não importam código do app, que pode mudar depois). A
operação reversa não faz nada (`RunPython.noop`): desfazer não deve apagar categorias que a pessoa
já pode ter editado.

**Rationale**: a migration roda sozinha na subida (`scripts/start-dev.sh`, spec 001), uma única
vez por banco (FR-002), e é testável com o banco de testes.

**Alternativas**: comando de gerenciamento manual (alguém precisa lembrar de rodar); criar na
primeira listagem (R-04).

**Teste da migration**: um teste com `MigrationExecutor` volta para `gastos.0001`, cria um usuário
sem categorias, avança para `0002` e confere as 7. O `pytest-django` permite isso com
`@pytest.mark.django_db(transaction=True)`.

---

## R-06 — Nome único sem diferenciar maiúsculas

**Decisão**:

- **No banco**: `UniqueConstraint(Lower("nome"), "dono", name="gastos_categoria_nome_por_dono",
  violation_error_message="Já existe uma categoria com este nome.")`.
- **Na API**: o DRF 3.18 só gera `UniqueTogetherValidator` para constraints com `fields`, não com
  expressões. Por isso o `CategoriaSerializer.validate_nome` confere
  `Categoria.objects.do_dono(usuario).filter(nome__iexact=nome).exclude(pk=instancia)` e devolve
  a mensagem no campo `nome` (FR-005).
- **Corrida** (dois envios iguais ao mesmo tempo): o `IntegrityError` da constraint é convertido
  para o mesmo 400 no campo `nome`, no `perform_create`/`perform_update` da viewset.

O nome é salvo sem os espaços das pontas (`CharField` do DRF já faz `trim_whitespace`), com no
máximo 50 caracteres (`max_length=50`). Comparação sem diferenciar maiúsculas, mas com acentos
("Saude" ≠ "Saúde"), como `iexact`/`Lower` fazem no PostgreSQL.

**Rationale**: a regra fica no banco (garantia) e na validação (mensagem no campo certo, junto com
os outros erros). É o caso previsto em R-05 da spec 004 ("cada recurso define a sua").

**Alternativas**: guardar o nome já em minúsculas (perde a grafia escolhida); citext (extensão do
PostgreSQL, uma migração a mais sem ganho).

---

## R-07 — Cor automática

**Decisão**: sem cor informada, `escolher_cor_livre(usuario)` devolve a primeira cor da paleta
que a pessoa ainda não usa; se todas estiverem em uso, a da posição `quantidade % 12`.

**Rationale**: categorias novas ganham cores diferentes das existentes enquanto houver cor livre,
o que ajuda os gráficos da US-24.

---

## R-08 — API

**Decisão**: `CategoriaViewSet(FiltroPorDonoMixin, ModelViewSet)` em `gastos/views.py`, com
`DefaultRouter` em `/api/categorias/`; ordenação `Lower("nome")`; ação `@action(detail=False)
cores` em `/api/categorias/cores/`, que devolve a paleta (exige sessão, como tudo). O kit
`CasosDeIsolamento` cobre o recurso (FR-009, constituição Princípio II), e a guarda de rotas da
spec 004 confere que a viewset usa o filtro por dono.

---

## R-09 — Tela de categorias

**Decisão**:

- **Rota** `/categorias`, filha do `Layout` atrás da `RotaProtegida` (spec 005); item "Categorias"
  no menu depois de "Início".
- **Hook** `useCategorias()` (`docs/arquitetura.md` §3: hooks por recurso): carrega a lista e a
  paleta, e expõe `criar`, `atualizar` e `excluir`, que recarregam a lista depois de cada operação
  (a ordem e a cor automática vêm sempre da API).
- **Formulário de criação** no topo (nome + seletor de cor + "Adicionar"); **edição na própria
  linha** (botão "Editar" troca a linha por um formulário com "Salvar" e "Cancelar").
- **Seletor de cor** `SeletorCor`: grupo de botões de rádio (`fieldset` com `legend` "Cor"), cada
  rádio com o nome da cor como rótulo acessível e uma amostra visual. Rádio nativo dá a navegação
  por setas e o foco pelo teclado sem código extra (FR-013).
- **Excluir** com `window.confirm("Excluir a categoria \"{nome}\"?")` (FR-012): nativo, acessível
  e simples; nos testes, `vi.spyOn(window, 'confirm')`.
- **Estados**: "Carregando categorias…", lista vazia com "Nenhuma categoria. Crie a primeira
  acima.", e falha de comunicação com a mensagem padrão (spec 005).

**Alternativas**: modal de edição (mais código e cuidado com foco); seletor `<input type="color">`
(livre, contraria a Q3); diálogo de confirmação próprio (mais código sem necessidade agora).

---

## Resumo de dependências

Nenhuma dependência nova, no backend nem na interface.
