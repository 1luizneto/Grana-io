# Quickstart de Validação: Telas de Login e Cadastro

**Feature**: `005-telas-login-cadastro` | **Plano**: [plan.md](plan.md)

Roteiro no navegador. O comportamento esperado está em
[contracts/interface.md](contracts/interface.md).

## Pré-requisitos

- Sistema no ar **com rebuild do frontend** (dependências novas):
  `docker compose up -d --build --wait`.
- Navegador em `http://localhost:5173`. Para os cenários com "aba anônima", use uma janela
  anônima (sem sessão guardada).
- Uma conta existente, por exemplo `ana@exemplo.com` / `uma-senha-boa-2026`.

## Cenários

### S1 — Suítes automatizadas (FR-020; constituição, Princípio IV)

```bash
sh testar.sh
```

**Esperado**: o script roda as duas suítes (backend e interface) e termina com sucesso; o backend
continua com os 163 testes da spec 004. Cada suíte também roda sozinha:
`docker compose run --rm backend pytest` e `docker compose run --rm frontend npm test`.

### S2 — Página protegida sem sessão (US2; FR-009; SC-004)

Numa aba anônima, abra `http://localhost:5173/`.

**Esperado**: vai direto para `/entrar`, sem mostrar nada da área protegida. O rodapé mostra o
estado da API.

### S3 — Login com erros e com sucesso (US1; FR-001, FR-003 a FR-005)

1. Clique em "Entrar" com tudo em branco → "Este campo é obrigatório." abaixo de cada campo.
2. Senha errada → "E-mail ou senha incorretos." acima do formulário; e-mail mantido, senha vazia.
3. Dados certos → página inicial com "Olá, Ana Souza!" (o cabeçalho com o nome chega na US4;
   conferido no S8 e no S9). Anote o tempo do login (SC-002: até 30 s).

### S4 — Sessão ao recarregar e ao reabrir (US2; FR-006; SC-003)

1. Recarregue a página → continua conectada, na mesma página.
2. Feche o navegador inteiro, abra de novo `http://localhost:5173/` → continua conectada.

### S5 — Volta para a página pedida (US2; FR-009)

Numa aba anônima, abra `http://localhost:5173/` (ou outra rota protegida), entre na tela de login
e confirme que volta para o endereço pedido.

### S6 — Renovação transparente e sessão expirada (US2; FR-007, FR-008)

1. Suba o backend com acesso curto: `GRANA_SESSAO_ACESSO_MINUTOS=1` no `.env` e
   `docker compose up -d backend`. Entre, espere 2 minutos e recarregue → continua conectada
   (a renovação aconteceu sem aviso). Nos logs do backend aparece **um** `POST /api/auth/renovar/`.
2. Com a sessão aberta, estrague as credenciais no DevTools (Application → Local Storage →
   `grana.sessao` → troque os valores de `acesso` e de `renovacao` por `x`) e recarregue → login
   com "Sua sessão expirou. Entre novamente." (o acesso é recusado, a renovação também).
3. Remova o `GRANA_SESSAO_ACESSO_MINUTOS` do `.env` e `docker compose up -d backend`.

### S7 — Cadastro (US3; FR-002, FR-003, FR-019; SC-001, SC-006)

1. Em `/entrar`, clique em "Criar conta".
2. Envie com o e-mail `ana@exemplo.com`, senha `123` e confirmação `456` → as três mensagens
   aparecem ao mesmo tempo, cada uma abaixo do seu campo; nome e e-mail mantidos, senhas vazias.
3. Envie com dados novos e válidos → entra direto e vê "Olá, {nome}!". Anote o tempo do cadastro
   completo, desde abrir "Criar conta" (SC-001: até 2 min).
4. Com `GRANA_CADASTRO_ABERTO=0` (e `docker compose up -d backend`), tente cadastrar → "O cadastro
   de novas contas está desativado neste sistema." acima do formulário. Volte o valor depois.

### S8 — Sair (US4; FR-011; SC-005)

1. Conectada, clique em "Sair" → `/entrar` com "Você saiu do sistema."
2. Use o "voltar" do navegador → continua no login.
3. Com o backend parado (`docker compose stop backend`), entre de novo antes, pare o backend e
   clique em "Sair" → vai para o login mesmo assim. Suba o backend de novo.
4. Com duas abas conectadas, saia numa e clique em algo (ou recarregue) na outra → a outra também
   vai para o login (edge case "várias abas").

### S9 — Layout e tela estreita (US5; FR-012, FR-013; SC-007)

1. Conectada, confira cabeçalho ("Grana.io", nome, "Sair") e menu ("Início").
2. No DevTools, modo dispositivo com 360 px de largura: login, cadastro e início sem rolagem
   horizontal, todos os campos e botões utilizáveis.
3. Só com o teclado (Tab, Enter): entrar e sair.

### S10 — Página não encontrada e regressão da spec 001 (FR-018)

1. Abra `http://localhost:5173/nao-existe` → "Página não encontrada." com link para o início.
2. Com o banco parado (`docker compose stop db`), abra `http://localhost:5173/entrar` → o rodapé
   informa que o banco está indisponível (spec 001). Suba o banco de novo.
3. Nenhum recurso de terceiros (FR-016): no DevTools, aba Rede, com cache desativado, recarregue
   login e início; todas as requisições vão para `localhost:5173`. E
   `grep -rnE "https?://" frontend/index.html frontend/src` não encontra URL externa (só
   comentários ou `localhost`).
