# Research: Cadastro de Usuário

**Feature**: `002-cadastro-usuario` | **Data**: 2026-09-30 | **Plano**: [plan.md](plan.md)

Decisões técnicas do Technical Context. Não restou nenhum "NEEDS CLARIFICATION".

---

## R-01 — Modelo de usuário próprio, identificado pelo e-mail

- **Decision**: criar o app `accounts` com o model `Usuario(AbstractBaseUser, PermissionsMixin)`,
  com `USERNAME_FIELD = "email"` e `REQUIRED_FIELDS = ["nome"]`, e definir
  `AUTH_USER_MODEL = "accounts.Usuario"`. Um `UsuarioManager` próprio implementa `create_user` e
  `create_superuser`.
- **Rationale**: a documentação do Django recomenda definir o modelo de usuário próprio **antes** da
  primeira migration que dependa dele, porque trocá-lo depois é trabalhoso. O banco hoje só tem
  dados de teste (spec, Assumptions). `AbstractBaseUser` evita os campos `username`, `first_name` e
  `last_name` do `AbstractUser`, que a spec não usa (nome é um campo único). `PermissionsMixin`
  mantém `is_superuser` e as permissões para o admin/US-04 sem retrabalho.
- **Alternatives considered**:
  - `AbstractUser` sem `username`: herda `first_name`/`last_name` inúteis e exige remover campos
    herdados.
  - Manter `auth.User` e usar o e-mail no campo `username`: frágil (limite de 150 caracteres,
    unicidade sensível a maiúsculas) e contradiz a constituição (login por e-mail).
  - Perfil separado (`OneToOne` com `auth.User`): adiciona um join em toda consulta e não resolve
    a identificação por e-mail.

## R-02 — Troca de `AUTH_USER_MODEL` num banco já migrado

- **Decision**: depois de implementar o model, **recriar o banco de desenvolvimento uma única vez**
  com `docker compose down -v`. A primeira subida aplica `accounts.0001` do zero.
- **Rationale**: a spec 001 já aplicou as migrations de `auth` (tabela `auth_user`). Como o `admin`
  não está instalado, nenhuma migration aplicada depende do modelo de usuário, e o Django não
  acusaria histórico inconsistente. Mesmo assim, a tabela `auth_user` ficaria órfã. Recriar o banco
  deixa o schema limpo, e não há dados reais a perder.
- **Alternatives considered**: migração manual de `auth_user` para `accounts_usuario`. É
  desnecessária sem dados reais.

## R-03 — E-mail único sem diferenciar maiúsculas, inclusive sob concorrência (FR-003, FR-004)

- **Decision**:
  - Normalizar sempre para `strip().lower()` num único ponto, `Usuario.normalizar_email()`,
    chamado pelo manager, pelo `save()` do model e pelo serializer.
  - Guardar o e-mail normalizado com `unique=True` (restrição no banco).
  - O serializer verifica a duplicidade antes, para devolver a mensagem junto com as demais
    validações (FR-008).
  - O service captura o `IntegrityError` da restrição, que só acontece quando dois cadastros
    simultâneos passam pela checagem, e o converte na mesma mensagem de e-mail duplicado.
- **Rationale**: a restrição no banco é a única garantia real contra corrida (US2, cenário 3). Com
  o e-mail já normalizado, um índice único simples basta, sem índice funcional `LOWER(email)`.
- **Alternatives considered**:
  - `UniqueConstraint(Lower("email"))`: funciona, mas é redundante se o valor gravado já é
    minúsculo, e complica o `get_by_natural_key` do login.
  - `CITEXT` do PostgreSQL: exige extensão e acopla o model ao Postgres.

## R-04 — Regras de senha (FR-005, FR-006)

- **Decision**: usar os validadores nativos do Django em `AUTH_PASSWORD_VALIDATORS`:
  - `UserAttributeSimilarityValidator` com `user_attributes=("nome", "email")`;
  - `MinimumLengthValidator` com `min_length=8`;
  - `CommonPasswordValidator`;
  - `NumericPasswordValidator`.

  Somar a eles um validador próprio, `accounts.validators.SenhaComumPtBrValidator`, com uma lista
  curta de senhas comuns em português que a lista do Django não cobre (ex.: `mudar123`,
  `brasil123`, `corinthians`). O máximo de 128 caracteres fica no serializer. A confirmação é
  comparada no `validate()` do serializer.
- **Rationale**: os validadores nativos cobrem mínimo, só números, senha comum e semelhança com
  dados pessoais, e já têm mensagens em pt-BR. **Verificado em 2026-09-30 no Django 5.2.17**: a lista
  do Django recusa `senha123`, `12345678` e `flamengo` com "Esta senha é muito comum.", mas
  **aceita** `mudar123`, `brasil123` e `corinthians`. O validador próprio fecha essa lacuna sem
  dependência nova, usando a mesma mensagem.
- **Alternatives considered**:
  - `CommonPasswordValidator(password_list_path=...)` apontando para uma lista pt-BR: substitui a
    lista padrão em vez de somar a ela.
  - Biblioteca de força de senha (`zxcvbn`): dependência nova sem necessidade presente
    (Princípio VI).

## R-05 — Armazenamento da senha (FR-007)

- **Decision**: manter o hasher padrão do Django, PBKDF2-SHA256 com sal aleatório e iterações
  atualizadas a cada versão, via `set_password()`.
- **Rationale**: atende ao "hash com sal" da spec e ao RNF-02 sem dependência nova. O Django
  atualiza o hash automaticamente no login quando as iterações mudam.
- **Alternatives considered**: Argon2 (`argon2-cffi`) é mais forte contra GPU, mas acrescenta
  dependência nativa. Pode entrar depois só com uma linha em `PASSWORD_HASHERS`, sem migração.

## R-06 — Senha fora de respostas, erros e logs (FR-007, SC-003)

- **Decision**:
  - `senha` e `confirmacao_senha` são campos `write_only` no serializer, e a resposta é montada
    por um serializer de saída que só tem `nome` e `email`.
  - A view de cadastro usa `@method_decorator(sensitive_post_parameters("senha", "confirmacao_senha"))`.
  - Nenhum log novo recebe os dados do cadastro.
- **Rationale**: no modo de desenvolvimento, a página de erro 500 do Django mostra os dados do POST
  a qualquer dispositivo da rede local (spec 001). O `sensitive_post_parameters` mascara esses
  campos nessa página e nos relatórios de erro.

## R-07 — Cadastro fechável por configuração (FR-012)

- **Decision**: a variável `GRANA_CADASTRO_ABERTO` (padrão `1`) é lida no settings como
  `CADASTRO_ABERTO = env_bool("GRANA_CADASTRO_ABERTO", True)`. A função
  `accounts.services.cadastro.cadastro_aberto()` lê o setting. A view verifica **antes** de
  validar os dados e, se estiver fechado, responde **403** com
  `{"detail": "O cadastro de novas contas está desativado neste sistema."}`. A variável entra no
  `compose.yaml` (`${GRANA_CADASTRO_ABERTO:-1}`) e no `.env.example`.
- **Rationale**: o 403 comunica "operação não permitida neste sistema", independente dos dados,
  e fica consistente com a spec ("mesmo que os dados sejam válidos"). Ler o setting a cada
  requisição permite testar com `override_settings`.
- **Alternatives considered**: 404 (esconder a rota) foi descartado, porque a spec pede mensagem
  clara. Um flag no banco, alterável pelo admin, fica para quando houver admin (US-04).

## R-08 — Contrato e rota (FR-001, FR-009)

- **Decision**: `POST /api/usuarios/`, pública (`AllowAny`, sem autenticação). Responde **201** com
  `{"nome": ..., "email": ...}`, **400** com erros por campo no formato padrão do DRF e **403**
  com o cadastro fechado. `GET` e os demais métodos respondem 405. Os campos de entrada são `nome`,
  `email`, `senha` e `confirmacao_senha`.
- **Rationale**: é REST orientado a recursos, com o plural em pt-BR (`docs/arquitetura.md` §4,
  "Nomenclatura"): criar um usuário é um `POST` na coleção. A US-04 poderá acrescentar
  `/api/usuarios/eu/` para o perfil sem conflito. Sem `id` na resposta, porque a spec pede "sem
  dados internos" e nenhum cliente precisa dele antes do login.
- **Alternatives considered**: `POST /api/auth/cadastro/` é orientado a ação, fora do padrão de
  recursos do projeto.

## R-09 — Camadas e o gancho para a US-05

- **Decision**:
  - A view fina (`CadastroView`) aplica o fechamento, valida com o `CadastroSerializer` e chama o
    application service `cadastrar_usuario(nome, email, senha) -> Usuario`.
  - O service executa dentro de `transaction.atomic()`, e é ali que a US-05 acrescentará a
    criação das categorias padrão, com chamada explícita.
  - Sem signals.
- **Rationale**: segue `docs/arquitetura.md` §2 (Application Service com `transaction.atomic`;
  signals não adotados). Atende à Assumption da spec: "permitir que a US-05 acrescente esse passo
  sem reescrever o fluxo".

## R-10 — Mensagens em pt-BR (FR-008, SC-004)

- **Decision**:
  - Usar as traduções pt-BR nativas do Django e do DRF, ativas por `LANGUAGE_CODE = "pt-br"`.
    Exemplos: "Este campo é obrigatório.", "Insira um endereço de email válido." e as mensagens
    dos validadores de senha.
  - Mensagens próprias para e-mail duplicado ("Já existe uma conta com este e-mail."), senhas
    diferentes ("As senhas não conferem."), senha comum pt-BR e cadastro fechado.
  - O nome só com espaços usa `error_messages["blank"] = "Este campo é obrigatório."`.
  - A senha não sofre `trim` (`trim_whitespace=False`), para que espaços façam parte dela.
- **Rationale**: o DRF, por padrão, diz "Este campo não pode ser em branco." para nome só com
  espaços, e a spec pede tratá-lo como obrigatório (US3, cenário 2). Cortar espaços da senha
  mudaria silenciosamente a credencial.
- **Textos nativos verificados (Django 5.2.17 / DRF 3.18.1)**: "Este campo é obrigatório.",
  "Insira um endereço de email válido.", "Certifique-se de que este campo não tenha mais de 150
  caracteres.", "Esta senha é muito curta. Ela precisa conter pelo menos 8 caracteres.", "Esta
  senha é inteiramente numérica.", "Esta senha é muito comum.".
- **Verificação**: os testes comparam os textos exatos das mensagens próprias. Para as nativas,
  verificam o campo e o trecho essencial (ex.: "8 caracteres"), para não quebrar em atualizações
  de tradução.

## R-11 — Dependências novas

Nenhuma. Django, DRF e pytest-django já estão no projeto (spec 001).
