# Research: Mês de Referência

**Feature**: `007-mes-referencia` | **Plano**: [plan.md](plan.md)

Segue a regra de dono da spec 004 e os padrões de API da spec 006 (categorias). Nenhuma
dependência nova.

---

## R-01 — Model `MesReferencia` no app `gastos`

**Decisão**: `MesReferencia(OwnedModel)` em `gastos/models.py`, com `mes`, `ano` e `fechado`.

- `mes = PositiveSmallIntegerField()` e `ano = PositiveSmallIntegerField()`, com
  `CheckConstraint` no banco (`mes` entre 1 e 12, `ano` entre 2000 e 2100): a regra vale mesmo fora
  da API (ex.: shell, migration de dados futura).
- `fechado = BooleanField(default=False)` (FR-001: nasce aberto).
- `UniqueConstraint(fields=["dono", "ano", "mes"], name="gastos_mes_unico_por_dono",
  violation_error_message="Este mês já foi criado.")`.
- `ordering = ["ano", "mes"]` (FR-003; ordem cronológica crescente).

**Rationale**: o mês é a "pasta" dos gastos do EP-02, então fica no mesmo app das categorias
(spec 006, R-01). Dois inteiros ordenam e filtram de forma trivial e cronológica.

**Alternativas**: um `DateField` com o dia 1 (precisa normalizar o dia e mostra uma data que não
existe na ideia de "mês"); texto "MM/AAAA" (ordena errado: "01/2027" antes de "12/2026").

---

## R-02 — Fechar e reabrir pelo `PATCH` do campo `fechado`

**Decisão**: a API aceita `PATCH /api/meses/{id}/` com `{"fechado": true}` ou `false`. Mês e ano
são aceitos só na criação: numa alteração, um valor **diferente** do atual é recusado no campo
("Não é possível alterar o mês ou o ano. Exclua o mês e crie de novo."); o mesmo valor é aceito,
para um `PUT` completo não falhar à toa (FR-006).

**Rationale**: mantém o recurso REST simples e compatível com o kit de isolamento da spec 004, que
exercita `PATCH` (alterar de outra conta → 404 idêntico). Fechar o que já está fechado é aceito
(estado final igual ao pedido; edge case da spec).

**Alternativas**: ações `POST /meses/{id}/fechar/` e `/reabrir/` (dois endereços a mais, e o `PATCH`
ficaria sem uso ou proibido, o que quebra o kit com 405 no lugar de 404).

---

## R-03 — Mês repetido: validador do DRF + corrida

**Decisão**: a constraint usa `fields` (sem expressão), então o DRF 3.18 gera o
`UniqueTogetherValidator` sozinho a partir do `dono` oculto (`RegistroComDonoSerializer`, spec 004)
e usa a `violation_error_message` da constraint: a resposta é
`400 {"non_field_errors": ["Este mês já foi criado."]}`. A corrida (dois pedidos iguais ao mesmo
tempo) vira o mesmo 400 no `perform_create`, como nas categorias (spec 006, R-06).

**Rationale**: comportamento já verificado na spec 004 (R-05) com a constraint `fields`; nada de
código extra no serializer.

---

## R-04 — Mensagens de campo

**Decisão**: `IntegerField` com `min_value`/`max_value` e mensagens próprias:

| Campo | Situação | Mensagem |
|---|---|---|
| `mes` | ausente ou vazio | "Este campo é obrigatório." |
| `mes` | fora de 1 a 12, ou não inteiro | "Informe um mês de 1 a 12." |
| `ano` | ausente ou vazio | "Este campo é obrigatório." |
| `ano` | fora de 2000 a 2100, ou não inteiro | "Informe um ano de 2000 a 2100." |

"10" (texto) é aceito como 10; "10.5" e "outubro" caem na mensagem de faixa, que já diz como
corrigir (FR-009).

---

## R-05 — Excluir mês fechado: 400 com `detail`

**Decisão**: o `destroy` da viewset recusa mês fechado com
`400 {"detail": "Reabra o mês antes de excluí-lo."}` (FR-005). A regra de gastos vinculados fica
para a US-07 (Clarifications).

**Rationale**: o `interpretarErro` da interface (spec 005) leva `detail` de um 400 para a mensagem
geral, então a US-27 mostra o texto sem código novo. 409 seria semanticamente bom, mas exigiria
tratar mais um status na interface.

---

## R-06 — Rótulo MM/AAAA na resposta

**Decisão**: a API devolve `rotulo` (`"10/2026"`), somente leitura, além de `mes` e `ano`
(FR-003). A interface exibe o rótulo sem formatar datas por conta própria (Princípio V).

---

## R-07 — Conversão de `IntegrityError` compartilhada

**Decisão**: extrair o `_salvar` da `CategoriaViewSet` (spec 006) para uma função
`salvar_ou_erro_de_unicidade(salvar, erro)` em `gastos/views.py`, usada pelas duas viewsets, cada
uma com a sua mensagem e o seu campo (`nome` para categoria, `non_field_errors` para mês).

**Rationale**: evita duplicar o bloco `atomic` + `except IntegrityError`; continua local ao app
(uma abstração no `core` só quando um segundo app precisar).

---

## Resumo de dependências

Nenhuma dependência nova.
