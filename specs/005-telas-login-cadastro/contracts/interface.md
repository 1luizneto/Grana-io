# Contrato: Interface de login, cadastro e layout

**Feature**: `005-telas-login-cadastro` | **Requisitos**: FR-001 a FR-020

Contrato da interface com a pessoa usuária (rotas, textos e comportamento) e de como ela usa a
API. A API não muda: os contratos usados são
[api-cadastro.md](../../002-cadastro-usuario/contracts/api-cadastro.md) e
[api-sessao.md](../../003-login-logout/contracts/api-sessao.md).

## Rotas

| Endereço | Tela | Sem sessão | Com sessão |
|---|---|---|---|
| `/entrar` | Login | mostra | vai para `/` |
| `/cadastro` | Cadastro | mostra | vai para `/` |
| `/` | Início (layout) | vai para `/entrar`, depois volta | mostra |
| qualquer outro | Página não encontrada | mostra | mostra |

Toda rota protegida criada pelas próximas USs entra como filha do layout, atrás da `RotaProtegida`.

## Textos fixos da interface

| Situação | Texto |
|---|---|
| Sessão não pode mais ser renovada | Sua sessão expirou. Entre novamente. |
| Depois de sair | Você saiu do sistema. |
| Cadastro aceito, login automático falhou | Conta criada. Entre com sua senha. |
| Falha de rede ou resposta inesperada | Não foi possível falar com o servidor. Tente novamente. |
| Endereço inexistente | Página não encontrada. (link "Voltar ao início") |
| Verificando a sessão ao abrir | Carregando… |
| Página inicial | Olá, {nome}! (e o aviso de que os recursos financeiros chegam nas próximas entregas) |

Rótulos: Login: "E-mail", "Senha", botão "Entrar", link "Criar conta". Cadastro: "Nome", "E-mail",
"Senha", "Confirme a senha", botão "Criar conta", link "Já tenho conta". Cabeçalho: "Grana.io",
nome da pessoa, botão "Sair". Menu: "Início". Botões em processamento: "Entrando…" e
"Criando conta…", desabilitados.

## Textos vindos da API (exibidos como estão)

| Origem | Onde aparece |
|---|---|
| 400 `{"campo": ["..."]}` | abaixo do campo correspondente, todas as mensagens |
| 400 `non_field_errors`, 401/403/429 `detail` | acima do formulário |

Exemplos: "E-mail ou senha incorretos.", "Muitas tentativas. Tente novamente em instantes.",
"O cadastro de novas contas está desativado neste sistema.", "Já existe uma conta com este
e-mail.", "As senhas não conferem.", "Este campo é obrigatório.".

## Uso da API

| Ação | Chamada | Sucesso | Falha |
|---|---|---|---|
| Entrar | `POST /api/auth/entrar/` | grava sessão, vai para a página pedida ou `/` | erros no formulário |
| Cadastrar | `POST /api/usuarios/` e, com 201, `POST /api/auth/entrar/` | grava sessão, vai para `/` | erros no formulário; se só o login falhar, vai para `/entrar` com o e-mail e o aviso |
| Verificar ao abrir | `GET /api/usuarios/eu/` (autenticada) | atualiza o nome | sessão expirada |
| Sair | `POST /api/auth/sair/` com a `renovacao` (autenticada) | apaga sessão, vai para `/entrar` | apaga sessão mesmo assim |
| Qualquer chamada autenticada | `Authorization: Bearer <acesso>` | — | 401 `token_not_valid` → renovação única e repetição; renovação recusada, 401 sem `code` ou `user_inactive` → sessão expirada |

A renovação (`POST /api/auth/renovar/`) acontece no máximo uma vez por vez, mesmo com várias
chamadas simultâneas ([research R-03](../research.md)). Se outra aba renovar primeiro, a interface usa a credencial nova que ela gravou, em vez de expirar a sessão.

## Acessibilidade e tela estreita

- Todo campo tem `<label>` visível; erros ligados ao campo por `aria-describedby`, com
  `aria-invalid="true"`; mensagens gerais em região `role="alert"`.
- Enter envia o formulário; tudo funciona só com o teclado.
- Sem rolagem horizontal a partir de 360 px de largura.
