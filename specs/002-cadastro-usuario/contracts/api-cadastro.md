# Contrato: Cadastro de usuário

**Feature**: `002-cadastro-usuario` | **Requisitos**: FR-001 a FR-013

## `POST /api/usuarios/`

Cria uma conta. Rota pública: é a única forma pública de criar usuários (FR-013).

| Item | Valor |
|---|---|
| Autenticação | Nenhuma (`AllowAny`, `authentication_classes = []`) |
| Métodos | `POST` (e `OPTIONS`). `GET`, `PUT`, `PATCH` e `DELETE` retornam `405` |
| Content-Type | `application/json` |
| Efeitos | Cria um `Usuario` ativo, sem privilégios, numa transação. Não autentica (FR-009) |

### Requisição

```json
{
  "nome": "Ana Souza",
  "email": "Ana@Exemplo.com",
  "senha": "uma-senha-boa-2026",
  "confirmacao_senha": "uma-senha-boa-2026"
}
```

| Campo | Regras |
|---|---|
| `nome` | obrigatório; espaços nas pontas removidos; 1 a 150 caracteres após o corte |
| `email` | obrigatório; formato válido; até 254; normalizado para minúsculas sem espaços; único |
| `senha` | obrigatório; 8 a 128 caracteres; sem corte de espaços; não só números; não comum; não parecida com nome/e-mail |
| `confirmacao_senha` | obrigatório; idêntica a `senha` |

### Respostas

**201 Created**: conta criada. A resposta **não** traz `id`, senha, confirmação nem credencial de
acesso.

```json
{
  "nome": "Ana Souza",
  "email": "ana@exemplo.com"
}
```

**400 Bad Request**: dados inválidos. Todas as mensagens vêm de uma vez, por campo, no formato
padrão do DRF (`docs/arquitetura.md` §4). Exemplos:

```json
{
  "email": ["Já existe uma conta com este e-mail."],
  "senha": ["Esta senha é muito curta. Ela precisa conter pelo menos 8 caracteres."],
  "confirmacao_senha": ["As senhas não conferem."]
}
```

```json
{
  "nome": ["Este campo é obrigatório."],
  "email": ["Insira um endereço de email válido."],
  "senha": ["Esta senha é muito comum.", "Esta senha é inteiramente numérica."]
}
```

**403 Forbidden**: cadastro fechado (`GRANA_CADASTRO_ABERTO=0`). A checagem vem antes da validação
dos dados.

```json
{
  "detail": "O cadastro de novas contas está desativado neste sistema."
}
```

**405 Method Not Allowed**: qualquer método além de `POST`/`OPTIONS`. Não existe listagem de
usuários.

### Garantias

- Um cadastro recusado (400/403) não cria conta nem dado associado (FR-008, SC-005).
- Dois `POST` simultâneos com o mesmo e-mail criam no máximo uma conta; o outro recebe 400 com
  "Já existe uma conta com este e-mail." (FR-004).
- `senha` e `confirmacao_senha` nunca aparecem em respostas, mensagens de erro, páginas de erro do
  modo de desenvolvimento nem logs (FR-007).

### Esquema (OpenAPI 3.1, trecho)

```yaml
paths:
  /api/usuarios/:
    post:
      summary: Cria uma conta de usuário
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/CadastroEntrada" }
      responses:
        "201":
          description: Conta criada
          content:
            application/json:
              schema: { $ref: "#/components/schemas/CadastroSaida" }
        "400": { description: Erros de validação por campo }
        "403": { description: Cadastro desativado neste sistema }
components:
  schemas:
    CadastroEntrada:
      type: object
      required: [nome, email, senha, confirmacao_senha]
      properties:
        nome: { type: string, maxLength: 150 }
        email: { type: string, format: email, maxLength: 254 }
        senha: { type: string, minLength: 8, maxLength: 128, writeOnly: true }
        confirmacao_senha: { type: string, writeOnly: true }
    CadastroSaida:
      type: object
      additionalProperties: false
      required: [nome, email]
      properties:
        nome: { type: string }
        email: { type: string, format: email }
```

## Variável de ambiente nova

| Variável | Consumidor | Padrão | Descrição |
|---|---|---|---|
| `GRANA_CADASTRO_ABERTO` | backend | `1` | `0` fecha o cadastro de novas contas (403). Não afeta contas existentes. |

Complementa [../../001-infra-docker/contracts/environment.md](../../001-infra-docker/contracts/environment.md).
Entra no `compose.yaml` e no `.env.example`.
