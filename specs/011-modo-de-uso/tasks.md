---

description: "Lista de tarefas da feature 011-modo-de-uso (RNF-09)"
---

# Tasks: Modo de Uso

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[contracts/modos.md](contracts/modos.md), [quickstart.md](quickstart.md)

**Tests**: infraestrutura validada pelo quickstart (Princípio IV); as suítes continuam verdes.

**Organization**: checkpoints com commit e push, sem trailers de IA. Modo autônomo.

---

## Phase 1: Setup

- [X] T001 Rodar `sh testar.sh` (449 + 152) e `docker compose version` (ponto de atenção 1)

  > **Resultado (2026-11-13)**: ✅ 449 + 152 verdes (rodada final da spec 010, mesmo código);
  > Docker Compose v5.3.1 (suporta `!reset`). Analyze em modo autônomo: nenhum achado crítico.

---

## Phase 2: User Story 1 - Subir no modo de uso (Priority: P1) 🎯 MVP

- [ ] T002 [US1] `backend/Dockerfile` com estágios `dev` (o atual) e `uso` ([R-02](research.md)); `gunicorn==23.0.0` em `backend/requirements.txt`; `backend/scripts/start-uso.sh`
- [ ] T003 [US1] `frontend/Dockerfile` com estágios `dev`, `build` e `uso`; `frontend/nginx.conf` ([R-03](research.md)); conferir `frontend/.dockerignore`
- [ ] T004 [US1] `compose.yaml` com `target: dev` nos dois builds; `compose.uso.yaml` ([R-01](research.md), [R-04](research.md), [R-05](research.md))
- [ ] T005 [US1] Validar S3 do [quickstart.md](quickstart.md) e S1 (suítes no modo de desenvolvimento)

**Checkpoint**: modo de uso sobe e funciona.

---

## Phase 3: User Story 2 - Não expor detalhes técnicos (Priority: P1)

- [ ] T006 [US2] Rodar `check --deploy` na imagem de uso e tratar os avisos em `backend/config/settings.py` ([R-06](research.md)); validar S4 e S5

**Checkpoint**: sem detalhes técnicos.

---

## Phase 4: User Story 3 - Chave obrigatória e troca de modo (Priority: P1)

- [ ] T007 [US3] Validar S2 (recusa sem chave) e S6 (volta ao desenvolvimento com as mesmas contagens)

---

## Phase 5: Polish

- [ ] T008 [P] README (seção "Modo de uso": quando usar, gerar a chave, comandos, diferenças) e `.env.example`
- [ ] T009 BACKLOG (RNF-09 ☑) e `DECISOES-AUTONOMAS.md`

**Commit recomendado**:

| Checkpoint | Mensagem sugerida |
|---|---|
| T001 | `docs: especifica o modo de uso (RNF-09)` |
| T005 | `feat: adiciona o modo de uso com gunicorn e nginx` |
| T006 | `fix: trata os avisos de implantação no modo de uso` |
| T009 | `docs: documenta o modo de uso e conclui RNF-09` |
