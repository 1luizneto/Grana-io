# Contrato: Comandos operacionais

**Feature**: `001-infra-docker` | **Requisitos**: FR-001, FR-002, FR-006, FR-014, FR-017

Estes são os comandos que o README MUST documentar. Todos rodam na raiz do repositório e exigem
apenas Docker com Compose v2.

| Operação | Comando | Resultado esperado | Afeta dados? |
|---|---|---|---|
| Subir (primeiro plano) | `docker compose up` | Constrói as imagens se preciso, sobe `db` → `backend` (após o banco ficar saudável e as migrations rodarem) → `frontend`. Logs no terminal. | Não |
| Subir (segundo plano) | `docker compose up -d --wait` | Igual ao anterior, mas retorna quando os serviços com healthcheck estão saudáveis. | Não |
| Parar | `docker compose down` | Remove os containers e a rede. **Mantém** o volume de dados. | Não |
| Reconstruir imagens | `docker compose up --build -V` | Reconstrói `backend`/`frontend` e recria os volumes anônimos (ex.: após mudar dependências). O `-V` (`--renew-anon-volumes`) é necessário para descartar o `node_modules` antigo do frontend, que fica num volume anônimo e seria reaproveitado. Não afeta o volume nomeado do banco. | Não |
| Rodar testes | `docker compose run --rm backend pytest` | Executa a suíte do backend num banco de teste temporário (`test_grana`) e mostra aprovado/reprovado. | Não (banco real intocado) |
| Ver logs | `docker compose logs -f [serviço]` | Mostra os logs dos serviços. | Não |
| Ver estado | `docker compose ps` | Lista os serviços e o estado de saúde. | Não |
| **Remover dados** | `docker compose down -v` | Remove containers **e o volume `grana_pgdata`**. A próxima subida começa com banco vazio. | **Sim, irreversível** |

## Endereços de acesso

| Recurso | Na própria máquina | Por outro dispositivo da rede |
|---|---|---|
| Interface | `http://localhost:5173` | `http://<IP-da-máquina>:5173` |
| API | `http://localhost:8000/api/` | `http://<IP-da-máquina>:8000/api/` |
| Verificação de saúde | `http://localhost:8000/api/health/` | `http://<IP-da-máquina>:8000/api/health/` |
| Banco de dados | não exposto | não exposto |

As portas mudam conforme `FRONTEND_PORT` e `BACKEND_PORT` ([environment.md](environment.md)).
