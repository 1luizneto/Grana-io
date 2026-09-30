# Feature Specification: Cadastro de Usuário

**Feature Branch**: `002-cadastro-usuario`

**Created**: 2026-09-30

**Status**: Draft

**Input**: User description: "US-01: Como novo usuário, quero criar uma conta com nome, e-mail e senha, para ter meu próprio espaço no sistema. Critérios: nome, e-mail e senha; e-mail único com mensagem clara para duplicados; senha com tamanho mínimo e confirmação; senha armazenada com hash; categorias padrão geradas no cadastro (ver US-05)."

## Clarifications

### Session 2026-09-30

- Q: As categorias padrão entram nesta spec ou ficam para a US-05? → A: Ficam para a US-05
  (Sprint 2). A US-05 passa a gerar as 7 categorias padrão no cadastro e também para os usuários
  criados antes dela. Esta spec entrega só a conta.
- Q: O cadastro fica sempre aberto a qualquer pessoa da rede local ou pode ser fechado? → A:
  Aberto por padrão, com uma configuração de ambiente para fechar. Com o cadastro fechado, novas
  tentativas são recusadas com mensagem clara.
- Q: Depois de criar a conta, a pessoa entra automaticamente ou faz login em seguida? → A: Não
  entra automaticamente. O cadastro só cria a conta e confirma, e a pessoa faz login em seguida
  (US-02). A tela da US-26 pode levar ao login com o e-mail preenchido.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criar uma conta (Priority: P1)

Uma pessoa que ainda não usa o Grana.io informa nome, e-mail, senha e a confirmação da senha e
cria a sua conta. A partir daí ela passa a existir no sistema, identificada pelo e-mail, e
poderá entrar com e-mail e senha quando o login estiver disponível (US-02).

**Why this priority**: Sem conta não há usuário, e sem usuário nenhum dado financeiro pode ter
dono (constituição, Princípio II). É a porta de entrada de todo o sistema.

**Independent Test**: Enviar um cadastro válido e verificar que (a) a resposta confirma a
criação e mostra nome e e-mail, sem a senha; (b) a conta passa a existir identificada pelo
e-mail; (c) a senha não aparece em lugar nenhum de forma legível.

**Acceptance Scenarios**:

1. **Given** um e-mail ainda não cadastrado, **When** a pessoa informa nome, e-mail, senha e confirmação iguais e válidas, **Then** a conta é criada e a resposta mostra o nome e o e-mail cadastrados, sem a senha.
2. **Given** uma conta recém-criada, **When** se consulta o que ficou armazenado, **Then** a senha não está legível: só existe uma forma protegida (irreversível) dela.
3. **Given** uma conta criada com `Maria@Exemplo.com`, **When** se consulta a conta, **Then** o e-mail está armazenado como `maria@exemplo.com`.
4. **Given** o cadastro foi concluído, **When** a pessoa tenta usar o sistema, **Then** a conta está ativa, sem etapa de confirmação por e-mail.
5. **Given** o cadastro foi concluído, **When** se verifica a resposta, **Then** ela não contém credencial de acesso: a pessoa ainda não está autenticada e entra pelo login (US-02).

---

### User Story 2 - Rejeitar e-mail já cadastrado (Priority: P1)

Se a pessoa tenta se cadastrar com um e-mail que já tem conta, o sistema recusa e explica o
motivo de forma clara, sem criar uma segunda conta.

**Why this priority**: O e-mail é a identidade do usuário. Duas contas com o mesmo e-mail
quebrariam o login (US-02) e o isolamento dos dados (US-03).

**Independent Test**: Cadastrar um e-mail, tentar cadastrar de novo o mesmo e-mail (inclusive
com letras maiúsculas diferentes) e verificar a recusa com mensagem clara e que continua
existindo uma única conta.

**Acceptance Scenarios**:

1. **Given** já existe conta com `ana@exemplo.com`, **When** alguém tenta se cadastrar com `ana@exemplo.com`, **Then** o cadastro é recusado com a mensagem "Já existe uma conta com este e-mail." associada ao campo e-mail.
2. **Given** já existe conta com `ana@exemplo.com`, **When** alguém tenta se cadastrar com `ANA@Exemplo.com` ou `  ana@exemplo.com  `, **Then** o cadastro é recusado da mesma forma.
3. **Given** dois cadastros com o mesmo e-mail enviados ao mesmo tempo, **When** ambos são processados, **Then** no máximo uma conta é criada e o outro recebe a mensagem de e-mail duplicado.

---

### User Story 3 - Validar os dados informados (Priority: P1)

Quando algum dado está ausente ou inválido, o sistema recusa o cadastro e diz, campo a campo, o
que corrigir, sem criar a conta.

**Why this priority**: Senhas fracas ou dados inconsistentes comprometem a segurança dos dados
financeiros (RNF-02) e a usabilidade (RNF-04: mensagens que dizem o que fazer).

**Independent Test**: Enviar cadastros com cada tipo de problema listado abaixo e verificar, para
cada um, a recusa com a mensagem no campo certo e que nenhuma conta foi criada.

**Acceptance Scenarios**:

1. **Given** um cadastro sem nome, sem e-mail, sem senha ou sem confirmação, **When** é enviado, **Then** é recusado com "Este campo é obrigatório." em cada campo ausente.
2. **Given** um nome composto só de espaços, **When** é enviado, **Then** é recusado como nome obrigatório.
3. **Given** um e-mail em formato inválido (ex.: `ana@`, `ana.exemplo.com`), **When** é enviado, **Then** é recusado com mensagem de e-mail inválido.
4. **Given** senha e confirmação diferentes, **When** o cadastro é enviado, **Then** é recusado com "As senhas não conferem." no campo de confirmação.
5. **Given** uma senha com menos de 8 caracteres, **When** o cadastro é enviado, **Then** é recusado informando o tamanho mínimo.
6. **Given** uma senha composta só de números, muito comum (ex.: `12345678`, `senha123`) ou muito parecida com o nome ou o e-mail, **When** o cadastro é enviado, **Then** é recusado explicando o motivo.
7. **Given** vários campos com problema ao mesmo tempo, **When** o cadastro é enviado, **Then** todas as mensagens são devolvidas juntas, cada uma no seu campo.

---

### Edge Cases

- **E-mail com espaços ou maiúsculas**: espaços nas pontas são removidos e o e-mail é comparado e
  armazenado em minúsculas (US2, cenário 2).
- **Nome com espaços nas pontas**: os espaços são removidos antes de salvar; nomes com acentos e
  caracteres de qualquer idioma são aceitos (ex.: "João D'Ávila").
- **Tamanhos máximos**: nome com até 150 caracteres; e-mail com até 254 caracteres (limite do
  formato de e-mail). Acima disso, o cadastro é recusado com mensagem indicando o limite.
- **Senha muito longa**: senhas de até 128 caracteres são aceitas.
- **Cadastros simultâneos com o mesmo e-mail**: no máximo um é aceito (US2, cenário 3).
- **Senha nunca devolvida nem registrada**: nem a resposta do cadastro, nem mensagens de erro,
  nem logs contêm a senha ou a confirmação (constituição, Princípio I).
- **Revelação de e-mail cadastrado**: a mensagem de e-mail duplicado permite descobrir que um
  e-mail tem conta. Isso é aceito por ser critério explícito do backlog e por o sistema rodar só
  na rede local; o login (US-02) usa mensagem genérica.
- **Pessoa já autenticada tentando se cadastrar**: tratado com o login (US-02); nesta spec o
  cadastro é sempre público.
- **Quem pode se cadastrar**: com o cadastro aberto (padrão), qualquer pessoa com acesso ao
  sistema na rede local; não há convite nem aprovação. Quem administra pode fechar o cadastro por
  configuração depois de criar as contas da casa (FR-012).
- **Cadastro fechado**: a tentativa é recusada com "O cadastro de novas contas está desativado
  neste sistema.", mesmo que os dados sejam válidos, e nenhuma conta é criada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Enquanto o cadastro estiver aberto, o sistema MUST permitir que qualquer pessoa, sem estar autenticada, crie uma conta informando nome, e-mail, senha e confirmação da senha.
- **FR-002**: Nome, e-mail, senha e confirmação MUST ser obrigatórios; o nome MUST ter ao menos um caractere além de espaços e no máximo 150 caracteres.
- **FR-003**: O e-mail MUST ter formato válido, até 254 caracteres, e MUST ser normalizado (sem espaços nas pontas, em minúsculas) antes de ser comparado e armazenado.
- **FR-004**: O e-mail MUST ser único entre todas as contas, sem diferenciar maiúsculas de minúsculas, inclusive sob cadastros simultâneos. Um e-mail já cadastrado MUST ser recusado com a mensagem "Já existe uma conta com este e-mail." associada ao campo e-mail.
- **FR-005**: A senha MUST ter no mínimo 8 e no máximo 128 caracteres, MUST NOT ser composta só de números, MUST NOT estar entre senhas muito comuns e MUST NOT ser muito parecida com o nome ou o e-mail.
- **FR-006**: A confirmação MUST ser idêntica à senha; caso contrário o cadastro MUST ser recusado com "As senhas não conferem." no campo de confirmação.
- **FR-007**: A senha MUST ser armazenada somente em forma protegida irreversível (hash com sal), nunca em texto legível, e MUST NOT aparecer em respostas, mensagens de erro ou logs.
- **FR-008**: Um cadastro recusado MUST NOT criar conta nem qualquer dado associado, e MUST devolver todas as mensagens de validação de uma vez, cada uma associada ao seu campo, em português e dizendo como corrigir.
- **FR-009**: Um cadastro aceito MUST responder confirmando a criação com o nome e o e-mail cadastrados e MUST NOT devolver a senha, dados internos nem qualquer credencial de acesso: o cadastro não autentica a pessoa, que entra depois pelo login (US-02).
- **FR-010**: A conta criada MUST ficar ativa imediatamente, identificada pelo e-mail, sem etapa de confirmação por e-mail (o sistema não envia e-mails).
- **FR-011**: A conta criada MUST NOT ter privilégios administrativos.
- **FR-012**: O cadastro MUST estar aberto por padrão e MUST poder ser fechado por configuração de ambiente, sem alterar código. Com o cadastro fechado, toda tentativa MUST ser recusada, sem criar conta, com a mensagem "O cadastro de novas contas está desativado neste sistema."; as contas existentes não são afetadas.
- **FR-013**: O cadastro MUST ser a única forma pública de criar contas; nenhuma outra operação sem autenticação pode criar ou alterar usuários.

### Key Entities

- **Usuário**: pessoa com conta no sistema. Atributos: nome, e-mail (único, normalizado, é o
  identificador de acesso), senha protegida, situação (ativa), data de criação. Não é
  administrador. Será o dono de todos os dados de domínio (US-03).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Uma pessoa com os dados em mãos conclui o cadastro em até 1 minuto na primeira tentativa, quando os dados são válidos.
- **SC-002**: 100% das tentativas de cadastro com e-mail já existente, em qualquer combinação de maiúsculas/minúsculas e espaços, são recusadas; o número de contas por e-mail nunca passa de 1.
- **SC-003**: Em nenhuma conta a senha pode ser lida a partir do que o sistema armazena, responde ou registra (verificável inspecionando armazenamento, respostas e logs).
- **SC-004**: Para cada tipo de dado inválido listado na US3, o cadastro é recusado e a mensagem aponta o campo e o que corrigir, em português, em 100% dos casos.
- **SC-005**: Nenhum cadastro recusado deixa conta ou dado associado criado.

## Assumptions

- Esta spec entrega a **capacidade de cadastro** e sua regra de negócio, verificável por
  requisição documentada no contrato da API. A tela de cadastro no navegador é a US-26 (spec 005),
  e o login com e-mail e senha é a US-02 (spec 003).
- **Categorias padrão fora do escopo** (Clarifications): o critério da US-01 "Ao criar a conta,
  as categorias padrão são geradas" fica com a US-05, que as gera no cadastro e também para as
  contas criadas antes dela. O cadastro desta spec deve permitir que a US-05 acrescente esse passo
  sem reescrever o fluxo.
- O e-mail é o identificador de acesso; não existe "nome de usuário" separado.
- O nome é um único campo livre (não há separação entre nome e sobrenome).
- As regras de senha (mínimo 8, não só números, não comum, não parecida com os dados pessoais)
  seguem as recomendações usuais para aplicações web e são suficientes para um sistema local.
- O sistema não envia e-mails (sem servidor de e-mail): não há confirmação de e-mail nem
  recuperação de senha por e-mail; a redefinição de senha esquecida pelo administrador é da US-04.
- O primeiro administrador do sistema, se necessário, é criado por comando no ambiente Docker,
  fora deste fluxo público.
- Limitação de tentativas de cadastro (proteção contra abuso) está fora do escopo: o sistema roda
  só na rede local doméstica (spec 001, Assumptions).
- Como o banco ainda só contém dados de teste, a forma como o usuário é identificado (por e-mail)
  pode ser definida agora sem migração de dados existentes.
