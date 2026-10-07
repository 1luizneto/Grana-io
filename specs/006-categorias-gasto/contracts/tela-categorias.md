# Contrato: Tela de Categorias

**Feature**: `006-categorias-gasto` | **Requisitos**: FR-011 a FR-014

Segue os padrões de tela da spec 005 ([interface.md](../../005-telas-login-cadastro/contracts/interface.md)):
erros da API exibidos como chegam, ao lado do campo; mensagens gerais em `role="alert"`; falha de
comunicação com "Não foi possível falar com o servidor. Tente novamente.".

## Rota e menu

| Endereço | Acesso | Menu |
|---|---|---|
| `/categorias` | exige sessão (dentro do `Layout`) | "Categorias", segundo item, depois de "Início" |

## Conteúdo

- Título "Categorias".
- **Formulário de criação** no topo: campo "Nome", seletor "Cor" e botão "Adicionar"
  ("Adicionando…" e desabilitado durante o envio). Depois de criar, o formulário volta ao vazio.
- **Lista** em ordem alfabética (a ordem vem da API): amostra da cor, nome, botões "Editar" e
  "Excluir". Os botões têm nome acessível com a categoria (ex.: "Editar Saúde", "Excluir Saúde").
- **Edição na linha**: "Editar" troca a linha por campo "Nome", seletor "Cor", "Salvar" e
  "Cancelar". Erros aparecem na própria linha.
- **Excluir**: confirmação nativa `Excluir a categoria "{nome}"?`; só exclui com "OK".

## Seletor de cor

`fieldset` com `legend` "Cor" e um botão de rádio por cor da paleta (vinda de
`GET /api/categorias/cores/`), cada um com o nome da cor como rótulo acessível (ex.: "Verde") e uma
amostra visual com o `hex`. Navegável por Tab e setas. Na criação, nenhuma cor marcada significa
"automática".

## Estados

| Situação | Texto |
|---|---|
| Carregando | Carregando categorias… |
| Lista vazia | Nenhuma categoria. Crie a primeira acima. |
| Falha ao carregar ou salvar | Não foi possível falar com o servidor. Tente novamente. |

## Tela estreita

A partir de 360 px: formulário em coluna, linhas da lista quebrando os botões para baixo do nome,
sem rolagem horizontal; as amostras de cor quebram em várias linhas.
