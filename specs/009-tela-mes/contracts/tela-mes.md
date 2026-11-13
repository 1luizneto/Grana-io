# Contrato: Tela do Mês

**Feature**: `009-tela-mes` | **Requisitos**: FR-001 a FR-013

Segue os padrões das specs 005 e 006: erros da API exibidos como chegam, ao lado do campo;
mensagens gerais em `role="alert"`; sucesso em `role="status"`; falha de comunicação com "Não foi
possível falar com o servidor. Tente novamente.".

## Rotas e menu

| Endereço | Comportamento |
|---|---|
| `/meses` | Escolhe o mês inicial e vai para `/meses/:id` (sem meses: estado vazio) |
| `/meses/:id` | Tela do mês; id fora da lista da pessoa → "Mês não encontrado." |

Menu: "Início", **"Gastos do mês"**, "Categorias".

## Estrutura da tela

1. Título "Gastos do mês".
2. **Seletor**: `select` "Escolher mês" (rótulos MM/AAAA; fechados com " (fechado)") e o formulário "Novo
   mês" (`select` "Mês" com os nomes dos meses, campo "Ano", botão "Criar mês" / "Criando…").
3. **Cabeçalho do mês** (`h2` com o rótulo, ex.: "10/2026") com a situação ("Aberto" ou "Fechado")
   e os botões "Fechar mês" / "Reabrir mês" e "Excluir mês".
4. **Totais** (`h2` "Totais"): "Total do mês" e lista por categoria (amostra da cor, nome, total,
   "1 gasto" / "N gastos"), como a API devolveu.
5. **Formulário** (`form` "Lançar gasto" ou "Editar gasto"): "Descrição", "Valor", "Data",
   "Categoria", "Forma de pagamento"; botões "Lançar" ("Lançando…") ou "Salvar alterações"
   ("Salvando…") e "Cancelar edição".
6. **Gastos** (`h2` "Gastos"): `select` "Filtrar por categoria" ("Todas as categorias" + categorias)
   e `select` "Ordenar por" ("Data (mais antigo)", "Data (mais recente)", "Maior valor", "Menor
   valor"); tabela com Data, Descrição, Categoria, Pagamento, Valor e Ações ("Editar <descrição>",
   "Excluir <descrição>").

## Textos

| Situação | Texto |
|---|---|
| Carregando meses | Carregando meses… |
| Sem meses | Nenhum mês criado. Crie o primeiro abaixo. |
| Mês fora da lista | Mês não encontrado. |
| Carregando gastos | Carregando gastos… |
| Mês sem gastos | Nenhum gasto neste mês. |
| Filtro sem gastos | Nenhum gasto nesta categoria. |
| Mês fechado | Mês fechado. Reabra o mês para lançar ou alterar gastos. |
| Sucesso | Gasto lançado. / Gasto atualizado. / Gasto excluído. / Mês criado. / Mês fechado. / Mês reaberto. / Mês excluído. |
| Confirmação de gasto | Excluir o gasto "{descrição}" de {valor em R$}? |
| Confirmação de mês | Excluir o mês {MM/AAAA}? |

## Mês fechado

Formulário de gasto desabilitado (`fieldset disabled`), sem os botões "Editar" e "Excluir" nas
linhas; "Reabrir mês" no lugar de "Fechar mês".

## Formatação

Valores em reais ("R$ 1.234,50"), datas DD/MM/AAAA, forma de pagamento pelo nome da API ("Pix") ou
"—" quando vazia. Nenhum valor é somado ou recalculado na tela.

## Tela de categorias (mudança)

"Excluir <nome>" abre um painel na linha: texto `Excluir a categoria "{nome}"?`, `select` "Mover os
gastos para" (outras categorias; "Outros" escolhida se existir) e botões "Excluir" e "Cancelar".
Sem outra categoria: "Não há outra categoria para receber gastos.".

## Tela estreita

A partir de 360 px, sem rolagem horizontal: formulários em coluna; tabela como cartões, cada célula
com o nome da coluna.
