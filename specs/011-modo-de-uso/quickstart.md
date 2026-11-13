# Quickstart de Validação: Modo de Uso

**Feature**: `011-modo-de-uso` | **Contrato**: [modos.md](contracts/modos.md)

Infraestrutura: validada por estes cenários (constituição, Princípio IV). Para não criar um `.env`
no computador do responsável, a validação passa a chave pela linha de comando
(`DJANGO_SECRET_KEY=... docker compose ...`), que tem o mesmo efeito.

## Cenários

### S1 — Suítes (modo de desenvolvimento)

`sh testar.sh` → verde.

### S2 — Recusa sem chave (US3)

`docker compose -f compose.yaml -f compose.uso.yaml up -d --build --wait` sem a variável →
para antes de subir, com a mensagem do contrato.

### S3 — Subir e usar (US1)

Contar contas, meses e gastos no banco. Subir o modo de uso com uma chave → todos os serviços
saudáveis; `http://localhost:5173` abre a interface (arquivos de `/assets/` com hash, poucos
pedidos), login funciona, a tela do mês carrega; `http://localhost:8000` não responde; os
processos da API são `gunicorn` e rodam como `grana`, o Nginx como `nginx`; contagens iguais às
de antes.

### S4 — Sem detalhes técnicos (US2)

`/api/nao-existe/` → resposta curta, sem lista de rotas; cabeçalho `Server` sem versão; página de
erro do Nginx sem versão; pedido com `Host: malicioso` pela interface ainda funciona (o Host é
fixado); `check --deploy` sem avisos.

### S5 — Login por dispositivo (FR-008)

Tentativas de login erradas pela interface contam o limite (`429` depois do limite), e o endereço
registrado é o de quem acessa, não o do Nginx.

### S6 — Voltar ao desenvolvimento (US3)

`docker compose up -d --build --wait` → modo de desenvolvimento de volta (Vite na 5173, API na
8000), contagens iguais. O ambiente fica como estava antes da validação.
