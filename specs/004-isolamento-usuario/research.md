# Research: Isolamento de Dados por Usuário

**Feature**: `004-isolamento-usuario` | **Plano**: [plan.md](plan.md)

Decisões técnicas para cumprir a spec com o menor código possível, seguindo a constituição
(Princípio II) e o `docs/arquitetura.md` (§2.2, "Abstract Base Model + Mixin").

---

## R-01 — Base comum: `core.models.OwnedModel` (abstrato)

**Decisão**: model abstrato `OwnedModel` em `core/models.py`, com um único campo:

- `dono = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="+", editable=False)`

E o manager `objects = RegistroDoDonoQuerySet.as_manager()`, com o método `do_dono(usuario)`.

- `on_delete=CASCADE` cumpre a FR-012 (conta removida leva os registros junto).
- `related_name="+"` evita conflito de nomes reversos entre os vários models que vão herdar
  (`Usuario.categorias`, `Usuario.gastos`...). As consultas partem sempre do registro
  (`Categoria.objects.do_dono(usuario)`), nunca do usuário.
- `editable=False` tira o campo dos formulários e dos `ModelSerializer` gerados
  automaticamente: o dono nunca entra pelo payload por descuido.
- A FK já cria índice em `dono_id`, que é o filtro de toda consulta.

**Rationale**: é exatamente o padrão já previsto no `docs/arquitetura.md`. O nome `OwnedModel` é
mantido porque é o nome usado no documento de arquitetura e citado nas próximas specs; o campo e
os métodos seguem o pt-BR (`dono`, `do_dono`).

**Alternativas consideradas**:
- *Campo `usuario` em vez de `dono`*: ambíguo em models que já se relacionam com outro usuário
  no futuro. "Dono" é o termo da constituição ("registro com dono").
- *Manager padrão já filtrado por um usuário "atual" (thread-local)*: esconde o filtro e quebra
  em comandos, testes e tarefas sem request. Rejeitado (efeito implícito, ver §5 do documento de
  arquitetura sobre signals).
- *`related_name="%(class)ss"`*: útil só se alguém consultar a partir do usuário, o que a regra
  desencoraja. YAGNI.

---

## R-02 — Filtro na API: `core.mixins.FiltroPorDonoMixin`

**Decisão**: mixin para views genéricas e viewsets do DRF:

- `get_queryset()` → `super().get_queryset().do_dono(self.request.user)`;
- `perform_create(serializer)` → `serializer.save(dono=self.request.user)`.

Como o DRF sempre chama `filter_queryset(self.get_queryset())` e `get_object()` parte do
`get_queryset()`, o filtro por dono roda **antes** de busca, filtros, paginação, leitura,
alteração e exclusão (FR-004, FR-005, FR-008). Registro de outra conta e registro inexistente
caem no mesmo `Http404` do `get_object_or_404`. Identificador mal formado (`/api/x/abc/`)
também vira 404, porque o `get_object_or_404` do DRF trata `ValueError` e `TypeError` como "não
encontrado".

**Ajuste da implementação (T017/T018)**: o DRF 3.18 repassa o texto do `Http404` do Django, e o
id inexistente respondia `"No ItemExemplo matches the given query."` (inglês, com o nome
interno do model), enquanto o mal formado respondia `"Não encontrado."`. O mixin passou a
sobrescrever `get_object()` e trocar todo `Http404` por `NotFound()`, que sai sempre como
`{"detail": "Não encontrado."}` (FR-005).

**Rationale**: um único lugar faz o filtro, e as viewsets das próximas USs herdam sem escrever
filtro à mão (SC-005). O mixin precisa vir **antes** da classe do DRF na herança
(`class GastoViewSet(FiltroPorDonoMixin, ModelViewSet)`), o que a guarda de rotas (R-06) verifica
indiretamente.

**Alternativas consideradas**:
- *Permissão de objeto (`has_object_permission`) devolvendo 403*: viola a regra do 404 e não
  filtra listas. Rejeitado.
- *Filtro em cada `get_queryset` escrito à mão*: é exatamente o esquecimento que a spec quer
  evitar.

---

## R-03 — Dono imutável e ignorado no payload: `RegistroComDonoSerializer`

**Decisão**: base `core.serializers.RegistroComDonoSerializer(ModelSerializer)` com
`dono = HiddenField(default=CurrentUserDefault())`.

- `HiddenField` **não lê** o valor enviado pelo cliente: `{"dono": 2}` no payload é ignorado
  (FR-002), em criação e em alteração (FR-003).
- O valor vem sempre de `request.user`, que é o mesmo dono do registro em uma alteração, já
  que o registro só é encontrado se for do usuário (R-02).
- O campo não aparece na resposta: a API nunca expõe identificadores de outras contas.
- Com o `dono` presente nos dados validados, o `UniqueTogetherValidator` gerado pelo DRF para
  `UniqueConstraint(fields=["dono", ...])` funciona sem código extra (R-05).

O `perform_create` do mixin (R-02) também passa `dono=request.user`, como defesa em
profundidade para serializers que não herdem da base.

**Alternativas consideradas**:
- *`read_only_fields = ["dono"]`*: o campo apareceria na resposta e o validador de unicidade por
  dono não teria o valor durante a validação.
- *Rejeitar com erro 400 quando o payload traz `dono`*: a spec decidiu ignorar (US3, cenário 2), e
  ignorar é o comportamento padrão do DRF para campos desconhecidos ou ocultos.

---

## R-04 — Referências só para registros do mesmo dono: `RelacionadoDoDonoField`

**Decisão**: `core.serializers.RelacionadoDoDonoField(PrimaryKeyRelatedField)`, cujo
`get_queryset()` aplica `do_dono(request.user)` sobre o queryset declarado. Um identificador de
outra conta e um inexistente produzem o mesmo erro de campo, com a mensagem própria
`"Registro não encontrado."` (FR-006).

**Rationale**: a mensagem padrão do DRF em pt-BR (`Pk inválido "{pk_value}" - objeto não
existe.`) é técnica. A mensagem própria segue a regra de erros "que digam como corrigir"
(`docs/arquitetura.md` §4) e é a mesma nos dois casos, sem vazar existência.

**Alternativas consideradas**: validar a referência no service. Funciona, mas cada US teria de
lembrar; no campo, a regra vem junto da declaração.

---

## R-05 — Unicidade por dono (FR-007)

**Decisão**: convenção para models com nome único: `UniqueConstraint(fields=["dono", "nome"],
name="...")`, nunca `unique=True` no campo isolado. Com o `HiddenField` de R-03, o DRF 3.18 gera
o `UniqueTogetherValidator` para a constraint, e o erro vira um 400 de validação, sem
`IntegrityError`.

**Verificado na implementação (T023)**: o DRF 3.18 usa a `violation_error_message` da constraint
(`ModelSerializer._get_constraint_violation_error_message`) quando ela é diferente da padrão do
Django. Por isso cada model define a sua (no exemplo, `"Já existe um grupo com este nome."`), e o
erro sai como `{"non_field_errors": [...]}` sem citar `dono`. Nenhum código extra no serializer
base. A consulta do validador filtra pelo valor de `dono`, que é sempre o usuário atual, então só
registros do próprio dono contam.

**Alternativas consideradas**: capturar `IntegrityError` na view. Rejeitado: vira 500 se alguém
esquecer, e o erro não sai no formato de campo.

---

## R-06 — Guardas automáticas (FR-010, US4)

**Decisão**: duas guardas na suíte, no estilo da guarda de rotas já existente
(`tests/accounts/test_protecao_api.py`):

1. **Guarda de models** (`tests/core/test_guarda_isolamento.py`): percorre
   `apps.get_models()` dos apps do projeto (os que estão dentro de `BASE_DIR`, excluindo
   bibliotecas) e exige que todo model concreto herde de `OwnedModel`, exceto uma lista
   explícita `MODELS_SEM_DONO = {"accounts.Usuario"}`. A lógica fica numa função pura
   (`modelos_sem_dono(models, excecoes)`, em `tests/isolamento.py`) com teste próprio do caso
   negativo: passar o `Usuario` sem a exceção faz a função apontá-lo (US4, cenário 1).

   **Exceções** (constituição v1.2.0, Princípio II): além do `Usuario`, só entram em
   `MODELS_SEM_DONO` os **dados de referência compartilhados**, que não pertencem a ninguém e são
   somente leitura pela API (ex.: faixas de INSS e IRRF por ano, US-15). Cada entrada leva um
   comentário com a spec que a criou, e o `plan.md` dessa spec justifica a exceção.
2. **Guarda de rotas**: percorre as rotas (mesma função do teste de proteção, extraída para
   `tests/rotas.py` como `rotas()`) e, para toda view cujo `queryset.model` herda de `OwnedModel`, exige que a view
   herde de `FiltroPorDonoMixin`. O teste usa `@pytest.mark.urls("tests.exemplo.urls")`, que
   inclui as rotas reais (`config.urls`) e as de exemplo; assim a guarda cobre a aplicação e
   pode ser demonstrada com a viewset de exemplo.

**Rationale**: SC-004 pede que um model sem dono seja detectado antes do merge. A segunda guarda
cobre o outro esquecimento provável, que é a viewset sem o mixin.

**Limite aceito**: a guarda não verifica se cada US escreveu os testes de isolamento (FR-011).
Isso é garantido pelo kit de R-08, pelo item no tasks.md de cada US e pelo "Constitution Check"
(Princípio II). Descobrir subclasses de teste em tempo de execução seria frágil (depende de quais
arquivos o pytest coletou).

---

## R-07 — Registro de exemplo só nos testes (FR-013)

**Decisão**: app Django de teste `tests/exemplo/` (sem pasta `migrations`), com:

- `GrupoExemplo(OwnedModel)`: `nome`, com `UniqueConstraint(dono, nome)` (R-05);
- `ItemExemplo(OwnedModel)`: `descricao`, `valor` (`DecimalField`, Princípio III) e
  `grupo` (FK opcional para `GrupoExemplo`, para provar a FR-006);
- serializers, uma `ItemExemploViewSet(FiltroPorDonoMixin, ModelViewSet)` com busca
  (`SearchFilter`, parâmetro `busca`) e a ação `total` (contagem e soma), e uma viewset de grupos;
- `tests/exemplo/urls.py`, que inclui `config.urls` e adiciona `/api/exemplo/...`.

O app entra no `INSTALLED_APPS` só em `config/settings_test.py` (que importa `config.settings` e
acrescenta `tests.exemplo`), usado pelo `pytest.ini`. As rotas entram só nos testes que pedem,
via `@pytest.mark.urls("tests.exemplo.urls")`.

- **Com migration inicial** (`tests/exemplo/migrations/0001_initial.py`). O plano era não ter
  migrations e deixar o `migrate --run-syncdb` criar as tabelas, mas a implementação (T009)
  mostrou que o Django cria as tabelas de apps sem migration **antes** de aplicar as migrations,
  e a FK `dono` → `accounts_usuario` falha ("relation accounts_usuario does not exist"). Com a
  migration, a ordem de dependência é respeitada.
- O banco de uso nunca vê o app nem a migration, porque o `settings.py` não o inclui: o
  `migrate` de uso não conhece o app `exemplo` (verificado: nenhuma tabela `exemplo_*` e nenhuma
  linha `exemplo` em `django_migrations`). O `makemigrations --check` passa com os dois settings.
- As rotas de exemplo também não passam pela guarda de proteção do `test_protecao_api.py`, que
  usa o `ROOT_URLCONF` real. Ainda assim, elas herdam a autenticação padrão.

**Rationale**: cumpre a decisão A da clarificação sem deixar rastro na aplicação.

**Alternativas consideradas**:
- *Models definidos dentro do arquivo de teste com `schema_editor`*: frágil, fora do padrão do
  pytest-django e sem rotas reais.
- *Variável de ambiente que liga o app no `settings.py`*: deixaria uma porta para o app aparecer
  no banco de uso. Rejeitado.

---

## R-08 — Kit de testes de isolamento reaproveitável (FR-011, SC-005)

**Decisão**: `tests/isolamento.py` com a classe base `CasosDeIsolamento`. Cada US de dados declara
uma subclasse com:

- `url_lista` e `url_detalhe` (função que monta a URL a partir do id);
- `criar(usuario)`: fixture ou fábrica que cria um registro para a conta informada;
- `payload_criacao` e `payload_alteracao`.

A subclasse herda os casos mínimos da FR-011: lista só do dono, lista vazia sem pistas, abrir,
alterar e excluir registro de outra conta (404 idêntico ao de id inexistente, registro intacto),
dono do payload ignorado na criação e na alteração.

**Rationale**: as próximas USs ganham os testes de isolamento escrevendo só a configuração. O
registro de exemplo (R-07) é o primeiro usuário do kit, o que prova que ele funciona.

**Alternativas consideradas**: copiar os testes em cada US. Rejeitado, porque é justamente onde a
cobertura se perde.

---

## R-09 — Fixtures compartilhadas

**Decisão**: mover `usuario`, `outro_usuario`, `cliente` e `cliente_autenticado` de
`tests/accounts/conftest.py` para `tests/conftest.py`, e acrescentar `cliente_da_bia`
(autenticado como `outro_usuario`). As fixtures passam a valer para `tests/core/` e
`tests/exemplo/`.

**Rationale**: o isolamento precisa de duas contas em qualquer app. `force_authenticate` é
suficiente aqui, porque a autenticação real já está coberta pela spec 003.

---

## R-10 — Respostas de erro

**Decisão**: usar os comportamentos padrão do DRF com `LANGUAGE_CODE = "pt-br"`, com uma exceção:

- 404: `{"detail": "Não encontrado."}`, padronizado pelo `FiltroPorDonoMixin.get_object()`
  (ver o ajuste em R-02; o padrão do DRF 3.18 vazava o nome do model em inglês);
- campo de referência inválido: mensagem própria de R-04;
- sem sessão: 401 da spec 003, antes de qualquer consulta (as classes de autenticação e
  permissão rodam antes do `get_queryset`).

**Verificado na implementação (T017)**: o texto do contrato vale para os três casos (outra
conta, inexistente e mal formado) só depois do ajuste do mixin.

---

## Resumo de dependências

Nenhuma dependência nova. Tudo usa Django 5.2 e DRF 3.18, já instalados.
