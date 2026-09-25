# Contrato: Verificação de saúde da API

**Feature**: `001-infra-docker` | **Requisitos**: FR-007, FR-008, US1 (cenários 2, 3 e 4)

## `GET /api/health/`

Informa se a API está no ar e se a conexão com o banco funciona. É a única rota pública desta
feature.

| Item | Valor |
|---|---|
| Autenticação | Nenhuma (`AllowAny`), exceção explícita à permissão global `IsAuthenticated` |
| Métodos | `GET` (também `HEAD` e `OPTIONS`, pelo DRF). Os demais retornam `405` |
| Content-Type | `application/json` |
| Efeitos colaterais | Nenhum (executa apenas `SELECT 1`) |

### Respostas

**200 OK**: API e banco operacionais

```json
{
  "status": "ok",
  "database": "ok"
}
```

**503 Service Unavailable**: API no ar, banco inacessível

```json
{
  "status": "error",
  "database": "unavailable"
}
```

**405 Method Not Allowed**: método diferente de `GET`/`HEAD`/`OPTIONS` (corpo padrão do DRF).

### Garantias

- O corpo tem **exatamente** as chaves `status` e `database`.
- Nenhuma resposta (inclusive a 503) contém mensagem de exceção, stack trace, host, porta, nome do
  banco, usuário ou senha.
- A rota responde tanto em acesso direto (`http://<host>:8000/api/health/`) quanto pelo proxy da
  interface (`http://<host>:5173/api/health/`).

### Esquema (OpenAPI 3.1, trecho)

```yaml
paths:
  /api/health/:
    get:
      summary: Verificação de saúde da API e do banco
      security: []
      responses:
        "200":
          description: API e banco operacionais
          content:
            application/json:
              schema: { $ref: "#/components/schemas/Saude" }
        "503":
          description: Banco inacessível
          content:
            application/json:
              schema: { $ref: "#/components/schemas/Saude" }
components:
  schemas:
    Saude:
      type: object
      additionalProperties: false
      required: [status, database]
      properties:
        status:   { type: string, enum: [ok, error] }
        database: { type: string, enum: [ok, unavailable] }
```

### Consumo pelo frontend

A página inicial chama `GET /api/health/` pelo cliente de API centralizado (`src/api/`) e exibe:

| Resultado da chamada | Mensagem exibida |
|---|---|
| 200, `database: ok` | API acessível (banco operacional) |
| 503 | API acessível, banco indisponível |
| Erro de rede / timeout / outro status | API inacessível |

Em nenhum caso a página quebra ou fica em branco (edge case "API fora do ar com a interface no ar").
