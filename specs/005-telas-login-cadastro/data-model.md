# Data Model: Telas de Login e Cadastro

**Feature**: `005-telas-login-cadastro` | **Plano**: [plan.md](plan.md)

Esta spec não cria nem altera dados no backend. O único dado novo vive no navegador.

## Sessão no navegador (`localStorage`, chave `grana.sessao`)

JSON com ([research R-02](research.md)):

| Campo | Tipo | Origem | Regras |
|---|---|---|---|
| `acesso` | texto | `POST /api/auth/entrar/` ou `/renovar/` | Enviado em `Authorization: Bearer`. Trocado a cada renovação. |
| `renovacao` | texto | idem | Usado só para renovar e para sair. Trocado a cada renovação (uso único, spec 003). |
| `usuario.nome` | texto | resposta do login; atualizado por `GET /api/usuarios/eu/` | Exibido no cabeçalho. |
| `usuario.email` | texto | idem | Identifica a conta na sessão (exibição e uso futuro, ex.: perfil na US-04). O preenchimento do login depois de um cadastro sem login automático usa o estado da navegação, porque nesse caso nada é gravado. |

**Nunca** contém a senha (FR-016).

**Validade**: um JSON que não tenha `acesso`, `renovacao` e `usuario.nome` como textos não vazios é
tratado como "sem sessão" e apagado.

## Estados da sessão (`AuthProvider`)

```text
                 sessão guardada                  /usuarios/eu/ 200
   [início] ───────────────────────▶ verificando ─────────────────────▶ conectado
      │                                   │                                │  ▲
      │ nada guardado                     │ renovação recusada / 401       │  │ entrar / cadastrar
      ▼                                   ▼                                │  │ e entrar (200)
 desconectado ◀──────────────────────────────────────────────────────────┘  │
      │         sair (sempre) / sessão expirada (renovação recusada)          │
      └───────────────────────────────────────────────────────────────────────┘
```

| Transição | Efeito no `localStorage` | Aviso na tela de login |
|---|---|---|
| entrar / cadastrar e entrar | grava a sessão | — |
| renovação (transparente) | troca `acesso` e `renovacao` | — |
| sessão expirada | apaga | "Sua sessão expirou. Entre novamente." |
| sair | apaga (mesmo sem resposta da API) | "Você saiu do sistema." |
| cadastro aceito, login automático falhou | nada gravado | "Conta criada. Entre com sua senha." (e-mail preenchido) |

## Formulários (estado local das telas)

| Tela | Campos | Depois de recusa |
|---|---|---|
| Login | `email`, `senha` | mantém `email`, apaga `senha` (FR-004) |
| Cadastro | `nome`, `email`, `senha`, `confirmacao_senha` | mantém `nome` e `email`, apaga as senhas (FR-004) |

Os nomes dos campos são os do contrato da API (specs 002 e 003), para que os erros de validação
devolvidos (`{"campo": [...]}`) caiam no campo certo sem tradução.
