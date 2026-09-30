# Data Model: Cadastro de Usuário

**Feature**: `002-cadastro-usuario` | **Data**: 2026-09-30 | **Plano**: [plan.md](plan.md)

## Usuario (`accounts.Usuario`)

Modelo de usuário do sistema (`AUTH_USER_MODEL = "accounts.Usuario"`). Base:
`AbstractBaseUser` + `PermissionsMixin` ([research R-01](research.md)). Tabela `accounts_usuario`.

| Campo | Tipo | Restrições | Origem |
|---|---|---|---|
| `id` | BigAutoField | PK | padrão do projeto |
| `email` | EmailField(254) | `unique=True`; sempre gravado normalizado (`strip().lower()`); é o `USERNAME_FIELD` | FR-003, FR-004, FR-010 |
| `nome` | CharField(150) | obrigatório; gravado sem espaços nas pontas; não pode ficar vazio após o corte | FR-002 |
| `password` | CharField(128) | hash PBKDF2 com sal (`set_password`); nunca texto legível | FR-007 |
| `is_active` | BooleanField | padrão `True` (conta ativa na criação) | FR-010 |
| `is_staff` | BooleanField | padrão `False` (cadastro público nunca é staff) | FR-011 |
| `is_superuser` | BooleanField | padrão `False` (via `PermissionsMixin`) | FR-011 |
| `groups`, `user_permissions` | M2M | via `PermissionsMixin`; sem uso nesta spec | admin/US-04 |
| `last_login` | DateTimeField | nulo; via `AbstractBaseUser`; preenchido pelo login (US-02) | — |
| `criado_em` | DateTimeField | `auto_now_add` | Key Entities ("data de criação") |

**Configuração do model**
- `USERNAME_FIELD = "email"`, `EMAIL_FIELD = "email"`, `REQUIRED_FIELDS = ["nome"]`.
- `objects = UsuarioManager()`:
  - `create_user(email, nome, password)` normaliza o e-mail e o nome, chama `set_password` e
    força `is_staff=False` e `is_superuser=False`;
  - `create_superuser(...)` usa `is_staff=True` e `is_superuser=True`, só por comando
    (`createsuperuser`), fora do fluxo público (FR-013; spec, Assumptions).
- `Usuario.normalizar_email(valor)` é o único ponto de normalização, usado pelo manager, pelo
  `save()` e pelo serializer ([research R-03](research.md)).
- `__str__` devolve o e-mail.

**Regras de validação** (aplicadas no cadastro; ver [contrato](contracts/api-cadastro.md))

| Regra | Onde | Mensagem |
|---|---|---|
| Campos obrigatórios | serializer | "Este campo é obrigatório." |
| Nome só com espaços | serializer (`blank`) | "Este campo é obrigatório." |
| Nome > 150 | serializer | nativa do DRF (limite de 150) |
| E-mail inválido / > 254 | serializer | "Insira um endereço de email válido." / nativa de limite |
| E-mail duplicado (qualquer caixa/espaços) | serializer + service (`IntegrityError`) | "Já existe uma conta com este e-mail." |
| Senha < 8, só números, comum, parecida com nome/e-mail | `AUTH_PASSWORD_VALIDATORS` + `SenhaComumPtBrValidator` | nativas em pt-BR / "Esta senha é muito comum." |
| Senha > 128 | serializer | nativa do DRF (limite de 128) |
| Confirmação diferente | serializer (`validate_confirmacao_senha`) | "As senhas não conferem." |

Todas as regras ficam no nível de campo, e nenhuma no `validate()` do serializer. Assim todos os
erros voltam juntos (FR-008; [research R-10](research.md)).

**Ciclo de vida nesta spec**: `(inexistente) → ativo`. Não há outras transições. Desativar, alterar
e excluir a conta ficam para specs futuras (US-04).

**Relacionamentos futuros**: `Usuario` será o dono (`OwnedModel.dono`) de todos os registros de
domínio a partir da US-03.

## Configuração

| Setting | Variável de ambiente | Padrão | Uso |
|---|---|---|---|
| `CADASTRO_ABERTO` | `GRANA_CADASTRO_ABERTO` | `True` (`1`) | Fecha o cadastro sem alterar código (FR-012, [research R-07](research.md)) |

## Migração

- A migration `accounts.0001_initial` é nova. Como `AUTH_USER_MODEL` muda, o banco de
  desenvolvimento deve ser recriado uma vez com `docker compose down -v`
  ([research R-02](research.md)).
