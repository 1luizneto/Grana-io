# Quickstart de Validação: Isolamento de Dados por Usuário

**Feature**: `004-isolamento-usuario` | **Plano**: [plan.md](plan.md)

Esta spec não tem rota nova na aplicação: o isolamento é provado pela suíte de testes, com o
registro de exemplo que só existe no banco de testes ([R-07](research.md)). O comportamento
esperado está em [contracts/isolamento.md](contracts/isolamento.md).

## Pré-requisitos

- Docker Desktop ligado e o sistema no ar (`docker compose up -d --wait`).
- Nenhuma dependência nova: não é preciso `--build`.

## Cenários

### S1 — Suíte completa verde (FR-011, FR-013; constituição, Princípio IV)

```bash
docker compose run --rm backend pytest
```

**Esperado**: todos os testes passam, incluindo os 126 das specs 001 a 003.

### S2 — Casos de isolamento com duas contas (US1 a US3; SC-001 a SC-003)

```bash
docker compose run --rm backend pytest tests/exemplo -v
```

**Esperado**: passam os casos do kit `CasosDeIsolamento` (lista só do dono, lista vazia,
abrir/alterar/excluir de outra conta → 404 idêntico ao inexistente, `dono` ignorado na criação e
na alteração) e os específicos do exemplo: busca e total só do dono, referência a grupo de outra
conta recusada com "Registro não encontrado.", nome de grupo repetido aceito entre contas e
recusado na mesma conta, identificador mal formado → 404, conta removida leva os registros.

### S3 — Guarda de models pega registro sem dono (US4; FR-010; SC-004)

1. Acrescente temporariamente, no fim de `backend/tests/exemplo/models.py`:

   ```python
   class Rascunho(models.Model):
       nome = models.CharField(max_length=10)
   ```

2. Rode `docker compose run --rm backend pytest tests/core/test_guarda_isolamento.py`.

**Esperado**: a guarda falha e a mensagem aponta `exemplo.Rascunho` como model sem dono.
Remova o trecho e rode de novo: passa.

### S4 — Guarda de rotas pega viewset sem filtro (US4)

1. Em `backend/tests/exemplo/views.py`, tire temporariamente o `FiltroPorDonoMixin` da
   `ItemExemploViewSet`.
2. Rode `docker compose run --rm backend pytest tests/core/test_guarda_isolamento.py`.

**Esperado**: a guarda falha e aponta a view (`ItemExemploViewSet`) com a primeira rota dela. Os testes de `tests/exemplo`
também falham (Bia passa a ver os itens de Ana). Desfaça e rode de novo: passa.

### S5 — Exemplo não existe no banco de uso nem na aplicação (FR-013)

```bash
docker compose exec -T db psql -U grana -d grana -c "\dt exemplo*"
docker compose run --rm backend python manage.py makemigrations --check --dry-run
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/exemplo/itens/
```

**Esperado**: "Did not find any relation named" (nenhuma tabela de exemplo); "No changes
detected"; `404` (rota inexistente na aplicação; a verificação de existência de rota vem antes
da autenticação).

### S6 — Nada mudou para quem usa (regressão das specs 001 a 003)

```bash
curl -s http://localhost:8000/api/health/
```

**Esperado**: `{"status": "ok", "database": "ok"}`. Login, renovação, saída e `/usuarios/eu/`
seguem cobertos pela suíte do S1.
