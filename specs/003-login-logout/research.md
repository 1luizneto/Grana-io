# Research: Login e Logout

**Feature**: `003-login-logout` | **Data**: 2026-09-30 | **Plano**: [plan.md](plan.md)

As verificações abaixo foram feitas em 2026-09-30 num container com o ambiente do projeto.
Não restou nenhum "NEEDS CLARIFICATION".

---

## R-01 — Biblioteca de sessão

- **Decision**: `djangorestframework-simplejwt==5.5.1` (traz `PyJWT` 2.15.1), com o app
  `rest_framework_simplejwt.token_blacklist`. O simplejwt fornece a credencial de acesso
  (`AccessToken`), a de renovação (`RefreshToken`), a autenticação por cabeçalho
  (`JWTAuthentication`) e a lista de bloqueio.
- **Rationale**: é a biblioteca fixada pela constituição (Stack: "JWT com
  djangorestframework-simplejwt"). A lista de bloqueio atende à renovação de uso único (FR-007) e à
  saída (FR-009) sem código próprio de persistência.
- **Verificado no código da 5.5.1**:
  - `JWTAuthentication.get_user` recusa usuário inativo (`CHECK_USER_IS_ACTIVE`), o que atende ao
    FR-014 para a credencial de acesso.
  - `TokenRefreshSerializer.validate` recusa renovação de conta inativa ("no_active_account"), o
    que atende ao FR-014 e à US4, cenário 4.
  - Token vencido lança `TokenError("Token is expired")`, e credenciais inválidas nas rotas
    protegidas respondem 401 com `"code": "token_not_valid"`.
  - O `TokenBlacklistSerializer` nativo bloqueia **qualquer** credencial de renovação recebida, sem
    checar de quem é. Por isso a saída é implementada à parte (R-05).
- **Alternatives considered**:
  - Sessão com cookie do Django: contraria a constituição (JWT) e exigiria CSRF.
  - `django-rest-knox`: tokens opacos no banco, outra dependência sem necessidade.

## R-02 — Mensagens próprias em pt-BR, simplejwt só como motor

- **Decision**: entrar, renovar e sair usam **serializers e views próprios** (`accounts`), com
  mensagens definidas no contrato. O simplejwt é usado só por dentro, para gerar e validar tokens e
  para a lista de bloqueio. Nas rotas protegidas, os erros de credencial seguem os textos pt-BR do
  próprio simplejwt (ex.: "O token informado não é válido para qualquer tipo de token"), porque
  quem os consome é a interface, pelo `code`.
- **Rationale — verificado no arquivo pt_BR do simplejwt 5.5.1**:
  - o login diria "Usuário e/ou senha incorreto(s)", mas a spec exige "E-mail ou senha
    incorretos." (FR-003);
  - a renovação diria "Token está na blacklist", um anglicismo.

  Com views próprias, os campos também ficam em pt-BR (`senha`, `acesso`, `renovacao`), coerentes
  com o cadastro (spec 002).
- **Alternatives considered**: subclassificar `TokenObtainPairSerializer`. O nome do campo de senha
  é fixo (`password`), o que exigiria contornar a inicialização da classe.

## R-03 — Autenticação por e-mail e mensagem genérica (FR-002, FR-003)

- **Decision**: o service `autenticar(email, senha)` chama `django.contrib.auth.authenticate(request,
  email=..., password=...)`.
  - O `ModelBackend` usa `Usuario.objects.get_by_natural_key`, que já normaliza o e-mail
    (spec 002).
  - O mesmo backend devolve `None` para e-mail inexistente, senha errada e conta inativa, e a view
    responde **401** `{"detail": "E-mail ou senha incorretos."}` nos três casos.
- **Rationale**: o `ModelBackend` roda o hasher de senha mesmo quando o e-mail não existe, o que
  reduz a diferença de tempo de resposta entre "e-mail inexistente" e "senha errada". O 401
  distingue "credenciais recusadas" de "dados faltando" (400).

## R-04 — Emissão, duração e renovação (FR-001, FR-005 a FR-008)

- **Decision**:
  - `SIMPLE_JWT`:
    - `ACCESS_TOKEN_LIFETIME = timedelta(minutes=GRANA_SESSAO_ACESSO_MINUTOS)`, padrão 30;
    - `REFRESH_TOKEN_LIFETIME = timedelta(days=GRANA_SESSAO_RENOVACAO_DIAS)`, padrão 7;
    - `ROTATE_REFRESH_TOKENS = True`, `BLACKLIST_AFTER_ROTATION = True`;
    - `UPDATE_LAST_LOGIN = False`, porque o próprio service atualiza (ver abaixo);
    - `AUTH_HEADER_TYPES = ("Bearer",)`;
    - `SIGNING_KEY = SECRET_KEY`, o padrão.
  - `emitir_sessao(usuario)` usa `RefreshToken.for_user(usuario)` e chama
    `django.contrib.auth.models.update_last_login` (FR-005).
  - `renovar_sessao(renovacao)` usa o `TokenRefreshSerializer` do simplejwt, que já recusa conta
    inativa, gira a credencial e bloqueia a antiga. Qualquer `TokenError`/`AuthenticationFailed`
    vira `SessaoInvalida`.
- **Rationale**: reaproveitar o serializer de renovação garante a sequência correta da biblioteca
  (validar → checar a conta → girar → bloquear a antiga). Os prazos vêm do ambiente (FR-006).
- **Chave de assinatura**: é a `SECRET_KEY`. Trocá-la invalida todas as sessões, o que é o
  comportamento esperado. O bloqueio da chave padrão fora do modo dev (spec 001) protege as
  credenciais.

## R-05 — Saída (FR-009; US5, cenário 4)

- **Decision**: `POST /api/auth/sair/` **exige credencial de acesso válida**. O service
  `encerrar_sessao(usuario, renovacao)` valida a credencial de renovação com `RefreshToken(valor)`
  (que já recusa vencida, adulterada ou bloqueada) e confere se `user_id` do token é o do usuário
  autenticado. Só então chama `token.blacklist()`. Qualquer falha vira 400
  `{"renovacao": ["Sessão inválida ou já encerrada."]}`, sem bloquear nada.
- **Rationale**: a spec exige recusar a credencial de renovação "de outra pessoa". O bloqueio
  nativo não faz essa checagem.
- **Consequência para a US-26**: se a credencial de acesso já tiver vencido, a interface renova
  antes de sair, ou simplesmente descarta as credenciais. A renovação expira sozinha em 7 dias.

## R-06 — Proteção das rotas e sessão vencida distinguível (FR-010, FR-011)

- **Decision**: `DEFAULT_AUTHENTICATION_CLASSES = [JWTAuthentication]`, com a permissão padrão
  `IsAuthenticated` que já existe (spec 001). As rotas públicas já declaram `AllowAny` com
  `authentication_classes = []`: saúde, cadastro, entrar e renovar. Respostas 401:
  - sem credencial: `{"detail": "As credenciais de autenticação não foram fornecidas."}` (texto
    pt-BR do DRF, verificado);
  - credencial vencida, adulterada ou de conta inativa: `"code": "token_not_valid"` ou
    `"user_inactive"`, do simplejwt.
- **Rationale**: a spec pede que a sessão vencida seja distinguível para a interface tentar
  renovar. A regra da interface é: 401 com `code == "token_not_valid"` → tenta renovar uma vez; se
  a renovação falhar → leva ao login. Distinguir "vencida" de "adulterada" não muda essa ação, e o
  campo `messages[].message` ainda informa "Token expirado" quando for o caso.
- Com `JWTAuthentication`, o DRF responde **401**, e não 403, para quem não está autenticado,
  porque há `authenticate_header` (`Bearer`).

## R-07 — Limite de tentativas no login (FR-015)

- **Decision**: throttle do DRF com escopo próprio. A classe
  `accounts.throttles.TentativasLoginThrottle(SimpleRateThrottle)` usa o escopo `"login"`,
  com taxa `f"{GRANA_LOGIN_TENTATIVAS_POR_MINUTO}/min"` (padrão 10) em
  `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`. Ela é aplicada só na view de entrar e conta todas as
  tentativas, certas ou erradas. Ao estourar, responde **429** com
  `{"detail": "Muitas tentativas. Tente novamente em instantes."}` e o cabeçalho `Retry-After`.
- **Mensagem**: o texto pt-BR nativo do DRF é "Pedido foi suprimido. Espera-se que esteja
  diponível em N segundos." (verificado, com erro de digitação), e não atende à spec. A view
  sobrescreve `throttled()` para lançar uma exceção `Throttled` própria, com a mensagem da spec,
  mantendo o `wait` para o `Retry-After`.
- **Armazenamento**: o cache padrão do Django (`LocMemCache`, em memória). Basta com o `runserver`
  de processo único. Os testes limpam o cache antes de cada caso.

## R-08 — Identificar o dispositivo atrás do proxy do Vite

- **Problema**: toda requisição feita pela interface chega ao backend vinda do container do
  `frontend` (proxy `/api`, spec 001 R-06). Sem tratamento, todos os dispositivos dividiriam o
  mesmo limite de tentativas.
- **Decision**:
  - O proxy do Vite passa a enviar `X-Forwarded-For` (`xfwd: true` em `vite.config.js`).
  - `TentativasLoginThrottle.get_ident` usa o **último** endereço do `X-Forwarded-For` **somente
    quando** `REMOTE_ADDR` é o do proxy confiável. Esse proxy é resolvido pelo nome de host
    `GRANA_PROXY_CONFIAVEL` (padrão `frontend`) via `socket.gethostbyname`, com cache curto.
  - Nos demais casos (acesso direto à porta 8000), usa `REMOTE_ADDR` e ignora o cabeçalho.
- **Rationale**: confiar no `X-Forwarded-For` de qualquer origem (`NUM_PROXIES = 1` do DRF)
  deixaria quem acessa a porta 8000 direto trocar de "dispositivo" só mudando o cabeçalho, e
  burlar o limite. Resolver o IP pelo nome do serviço funciona mesmo que o Docker troque o IP do
  container.
- **Verificar na implementação**: que o proxy do Vite 8 aceita `xfwd`. Se não aceitar, usar
  `configure: (proxy) => proxy.on("proxyReq", …)` para definir o cabeçalho.

## R-09 — Rotas e nomes

- **Decision**:

  | Ação | Rota | Autenticação |
  |---|---|---|
  | Entrar | `POST /api/auth/entrar/` | pública |
  | Renovar | `POST /api/auth/renovar/` | pública (usa a credencial de renovação) |
  | Sair | `POST /api/auth/sair/` | exige acesso |
  | Própria conta | `GET /api/usuarios/eu/` | exige acesso |

  Os campos são `email` e `senha` (entrada), `acesso` e `renovacao` (credenciais) e `usuario`
  (`nome` e `email`).
- **Rationale**: a sessão é ação, e não recurso de domínio, por isso fica agrupada em `/api/auth/`,
  com verbos em pt-BR (`docs/arquitetura.md` §4, "Nomenclatura"). A consulta da própria conta é um
  recurso e fica em `/api/usuarios/eu/`, rota antecipada na spec 002 (R-08) para a US-04.

## R-10 — Configuração nova

| Variável | Padrão | Uso |
|---|---|---|
| `GRANA_SESSAO_ACESSO_MINUTOS` | `30` | Duração da credencial de acesso |
| `GRANA_SESSAO_RENOVACAO_DIAS` | `7` | Duração da credencial de renovação |
| `GRANA_LOGIN_TENTATIVAS_POR_MINUTO` | `10` | Limite de tentativas de login por dispositivo |
| `GRANA_PROXY_CONFIAVEL` | `frontend` | Host cujo `X-Forwarded-For` é aceito |

Um novo helper `env_int(nome, padrao)` em `config/env.py`, com testes, rejeita valores não inteiros
ou menores que 1 com `ImproperlyConfigured`, citando a variável.

## R-11 — Testes sem dependência de relógio

- **Decision**: para testar credencial vencida, gerar o token e chamar
  `token.set_exp(lifetime=-timedelta(seconds=1))`. Para o limite de tentativas, usar
  `override_settings` na taxa e limpar o cache (`django.core.cache.cache.clear()`) num fixture.
- **Rationale**: dispensa `freezegun` (Princípio VI).

## R-12 — Dependências novas

| Dependência | Justificativa |
|---|---|
| `djangorestframework-simplejwt==5.5.1` | Obrigatória pela constituição (JWT). Lista de bloqueio incluída. Traz `PyJWT`. |

O app `token_blacklist` cria as tabelas `token_blacklist_outstandingtoken` (guarda as credenciais
de renovação emitidas) e `token_blacklist_blacklistedtoken`. Credenciais vencidas podem ser
removidas com `python manage.py flushexpiredtokens`, o que fica documentado no README.
