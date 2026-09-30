# Grana.io

Sistema de controle financeiro pessoal que roda **inteiramente no seu computador**: gastos,
rendas e cenários de salário (CLT, PJ, líquido direto) ficam num banco PostgreSQL local, e
nenhum dado é enviado a serviços externos.

O sistema tem três partes, todas em containers Docker:

| Parte | Tecnologia | Endereço padrão |
|---|---|---|
| Interface web | React + Vite | http://localhost:5173 |
| API | Django + Django REST Framework | http://localhost:8000/api/health/ |
| Banco de dados | PostgreSQL 17 | não fica acessível fora do Docker |

> Estado atual: fundação do projeto (Sprint 1). A interface mostra só uma página inicial
> provisória, e a API expõe só a verificação de saúde. O restante chega nas próximas entregas
> (ver [BACKLOG.md](BACKLOG.md)).

---

## 1. Pré-requisitos

- **Docker** com **Docker Compose v2**: [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  no Windows/macOS, ou Docker Engine + plugin Compose no Linux.
- O Docker precisa estar **em execução** (no Windows, abra o Docker Desktop e espere ele
  indicar que está pronto).
- Git, para clonar o repositório.

Não é preciso instalar Python, Node nem PostgreSQL na máquina.

## 2. Subir o sistema

Na pasta do repositório:

```bash
docker compose up
```

Na primeira vez, o Docker baixa as imagens e instala as dependências, o que pode levar alguns
minutos. Nas vezes seguintes, sobe em segundos. Os logs ficam no terminal; para parar, use
`Ctrl+C`.

Para subir em segundo plano e liberar o terminal:

```bash
docker compose up -d --wait
```

O comando só retorna quando banco e API estão saudáveis. A estrutura do banco é criada ou
atualizada automaticamente a cada subida; não há passo manual.

**Reconstruir as imagens**: depois de mudar dependências (`requirements*.txt`, `package.json`)
ou os arquivos `frontend/index.html` e `frontend/vite.config.js`, rode:

```bash
docker compose up --build
```

Isso não afeta os dados do banco. Alterações no código Python (`backend/`) e em
`frontend/src/` aparecem sozinhas, sem reconstruir.

## 3. Acessar

| Recurso | Endereço |
|---|---|
| Interface | http://localhost:5173 |
| Verificação de saúde da API | http://localhost:8000/api/health/ |

Todas as rotas da API ficam sob `http://localhost:8000/api/`. O endereço base sozinho responde
404, porque não é uma rota. Por enquanto a única rota é a verificação de saúde.

A verificação de saúde responde `{"status": "ok", "database": "ok"}` quando tudo está no ar,
ou HTTP 503 com `{"status": "error", "database": "unavailable"}` quando o banco não responde. A
página inicial da interface mostra esse mesmo estado.

## 4. Acessar por outro dispositivo da rede (ex.: celular)

A interface e a API também respondem pelo IP do computador, para outros dispositivos **da mesma
rede local**:

1. Descubra o IP atual do computador:
   - Windows: `ipconfig` → "Endereço IPv4" do adaptador em uso (ex.: `192.168.0.10`);
   - Linux: `ip addr` (ou `hostname -I`).

   O IP **muda quando você troca de rede** (casa, trabalho) e às vezes quando o roteador
   reinicia. Confira de novo antes de acessar; nada precisa ser reconfigurado no Grana.io.
2. No outro dispositivo, abra `http://<IP>:5173` (ex.: `http://192.168.0.10:5173`).
   Use o **IP**: nomes como `meu-pc.local` são recusados pelo servidor da interface
   ("Blocked request. This host is not allowed").
3. Se não abrir, verifique no Windows:
   - **Perfil da rede como "Privada"**: Configurações → Rede e Internet → (Wi-Fi ou Ethernet) →
     Tipo de perfil de rede → **Privada**. Só faça isso em redes confiáveis (sua casa).
   - **Firewall liberando as portas TCP 5173 e 8000** no perfil privado. Em um PowerShell
     **como administrador**:

     ```powershell
     New-NetFirewallRule -DisplayName "Grana.io (5173, 8000)" -Direction Inbound -Protocol TCP -LocalPort 5173,8000 -Action Allow -Profile Private
     ```

> **Somente rede local.** Não exponha o Grana.io à internet (redirecionamento de portas no
> roteador, túneis): o sistema roda em modo de desenvolvimento e não foi preparado para isso.

## 5. Parar

```bash
docker compose down
```

Encerra todos os containers. **Os dados do banco são mantidos** e voltam na próxima subida.

## 6. Rodar os testes

```bash
docker compose run --rm backend pytest
```

A suíte roda num banco de teste temporário, separado do banco real: os seus dados não são
lidos nem alterados. Pode ser executada com o sistema no ar ou parado.

## 7. Personalizar a configuração

O sistema funciona **sem nenhum arquivo de configuração**, com valores padrão de
desenvolvimento. Para personalizar (senha do banco, portas, chave secreta etc.):

1. Copie o exemplo:
   - Windows (PowerShell): `Copy-Item .env.example .env`
   - Linux/macOS: `cp .env.example .env`
2. Edite o `.env` e mude só o que precisar. Variáveis ausentes ou vazias usam o padrão.
3. Suba de novo com `docker compose up -d --wait`.

O `.env` **nunca é versionado** (está no `.gitignore`). Todas as variáveis estão comentadas no
[`.env.example`](.env.example). Pontos de atenção:

- **`POSTGRES_PASSWORD` só vale na primeira subida**, quando o banco é criado. Para trocar a
  senha depois, é preciso remover os dados (seção 8) e subir de novo.
- **`DJANGO_ALLOWED_HOSTS`**: se trocar o padrão `*`, inclua `localhost` e `backend`, além do IP
  da máquina (ex.: `localhost,backend,192.168.0.10`). Sem eles, a API fica marcada como não
  saudável e a interface mostra "API inacessível".
- **`DJANGO_DEBUG=0`** exige uma `DJANGO_SECRET_KEY` própria: com a chave padrão, a API se
  recusa a subir e informa qual variável definir.
- **Porta ocupada**: troque `FRONTEND_PORT` ou `BACKEND_PORT`.

## 8. Remover os dados locais

> ⚠️ **Irreversível.** Apaga todo o banco local (gastos, rendas, cenários, usuários). Não há
> como desfazer.

```bash
docker compose down -v
```

Na próxima subida, o banco começa vazio.

**Não use `docker volume prune`** para limpar o Docker: ele apaga os volumes de **todos** os
projetos que estiverem parados no momento, não só os do Grana.io.

## 9. Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `docker compose up` falha com erro de conexão com o Docker | Docker não está em execução | Abra o Docker Desktop (ou `sudo systemctl start docker` no Linux) e tente de novo. |
| Erro "port is already allocated" / "address already in use" | Outra aplicação usa a porta 5173 ou 8000 | Defina `FRONTEND_PORT` ou `BACKEND_PORT` no `.env` (seção 7). |
| Página inicial mostra **"API inacessível"** | Backend parado, ainda subindo ou `DJANGO_ALLOWED_HOSTS` sem `localhost`/`backend` | Veja `docker compose ps` e `docker compose logs backend`; corrija o `.env` se for o caso. |
| Página inicial mostra **"API acessível, banco indisponível"** | O container do banco parou | `docker compose up -d --wait` e, se persistir, `docker compose logs db`. |
| API não sobe após trocar `POSTGRES_PASSWORD` | A senha só vale na criação do banco | Volte a senha antiga no `.env` ou remova os dados (seção 8). |
| "Blocked request. This host is not allowed" | Acesso por nome de host em vez de IP | Acesse por `http://<IP>:5173` (seção 4). |
| Outro dispositivo fica carregando sem abrir | IP mudou, rede como "Pública", firewall ou roteador isolando dispositivos | Confira o IP, o perfil e o firewall (seção 4). Algumas redes (corporativas, de visitantes) bloqueiam a comunicação entre dispositivos. |
| Mudança em `index.html`, `vite.config.js` ou dependências não aparece | Esses arquivos ficam dentro da imagem | `docker compose up --build` |

Para ver os logs: `docker compose logs -f` (ou `docker compose logs -f backend`).

## 10. Documentação do projeto

- [BACKLOG.md](BACKLOG.md): histórias, requisitos e planejamento das sprints.
- [docs/arquitetura.md](docs/arquitetura.md): arquitetura e padrões de projeto.
- [.specify/memory/constitution.md](.specify/memory/constitution.md): princípios do projeto.
- [specs/](specs/): especificação, plano e tarefas de cada entrega.
