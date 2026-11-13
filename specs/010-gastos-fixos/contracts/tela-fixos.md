# Contrato: Tela de Gastos Fixos

**Feature**: `010-gastos-fixos` | **Requisitos**: FR-003, FR-006, FR-007, FR-009

Padrões das specs 005, 006 e 009 (erros da API ao lado do campo; `role="alert"` para erros gerais;
`role="status"` para sucesso; falha de comunicação com a mensagem padrão).

## Rota e menu

`/fixos`, com sessão. Menu: "Início", "Gastos do mês", **"Gastos fixos"**, "Categorias".

## Conteúdo

- Título "Gastos fixos" e o texto "Os gastos fixos ativos entram sozinhos em cada mês novo."
- **Formulário** (`form` "Novo gasto fixo" / "Editar gasto fixo"): "Descrição", "Valor", "Dia de
  vencimento", "Categoria", "Forma de pagamento", "Início" (`type="month"`, padrão: mês de hoje) e
  "Fim (opcional)" (`type="month"`). Botões "Cadastrar" ("Cadastrando…") ou "Salvar alterações"
  ("Salvando…") e "Cancelar edição".
- **Lista** (`ul`), um item por fixo: descrição, valor (R$), "dia N", categoria, período ("desde
  11/2026" ou "de 11/2026 a 01/2027") e "Inativo" quando desativado; botões "Editar X",
  "Desativar X" / "Reativar X" e "Excluir X".

## Textos

| Situação | Texto |
|---|---|
| Carregando | Carregando gastos fixos… |
| Lista vazia | Nenhum gasto fixo. Cadastre o primeiro acima. |
| Sucesso | Gasto fixo cadastrado. / Gasto fixo atualizado. / Gasto fixo desativado. / Gasto fixo reativado. / Gasto fixo excluído. |
| Confirmação | Excluir o gasto fixo "{descrição}"? Os gastos já lançados continuam. |

## Tela do mês (mudanças)

- Formulário "Lançar gasto": caixa "Repetir todo mês" (só ao lançar). Com ela: `"repetir": true`
  e o retorno "Gasto lançado e cadastrado como fixo.".
- Tabela: gastos com `fixo` mostram a marca "fixo" junto da descrição.
- "Mês criado." continua igual; os gastos gerados aparecem na tabela e nos totais.
