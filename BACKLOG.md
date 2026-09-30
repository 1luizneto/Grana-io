# Product Backlog Completo — Grana.io

**Projeto:** Grana.io — sistema web de controle financeiro pessoal com cadastro de gastos mensais por categoria e simulação de cenários de salário
**Entrega final:** Dezembro de 2026
**Stack:**
- Backend: Python (Django + Django REST Framework);
- Frontend: React;
- Banco de dados: PostgreSQL local (container Docker com volume persistente);
- Infraestrutura: Docker Compose (execução 100% local; hospedagem em nuvem fica como backlog futuro).

**Divisão de tempo:** 6 sprints de 15 dias, sugestão de início 01/10/2026, sugestão de término 29/12/2026

---

## Plano de Sprints (6 × 15 dias)

| Sprint | Período | Tema | Itens | Pts |
|---|---|---|---|---|
| S1 | 01/10 – 15/10 | Fundação: Docker + esqueleto + login | RNF-01, RNF-02, US-01, US-02, US-03, US-26 | 28 |
| S2 | 16/10 – 30/10 | Categorias e cadastro do mês + modo de uso | US-05, US-06, US-07, US-07b, US-08, RNF-03, RNF-09, US-27 | 34 |
| S3 | 31/10 – 14/11 | Cenários de ganho + cálculo CLT | US-11, US-12, US-13, US-14, US-15, US-16, US-28 | 31 |
| S4 | 15/11 – 29/11 | Motor de cálculo + PJ + comparação | US-13b, US-16b, US-17, US-18, US-19, US-21, US-29 | 37 |
| S5 | 30/11 – 14/12 | Recursos avançados + dashboard | US-09, US-10, US-10b, US-20, US-22, US-23, US-24, US-30 | 42 |
| S6 | 15/12 – 29/12 | Refinamento e qualidade final | US-04, US-25, RNF-04, RNF-05, RNF-06, RNF-07 | 24 |

**Total planejado:** 196 pts (RNF-08 fica fora das sprints — backlog futuro).

---

## Tabela de Épicos

| ID | Épico |
|---|---|
| EP-01 | Autenticação e Usuários |
| EP-02 | Categorias e Cadastro do Mês (Gastos) |
| EP-03 | Ganhos e Cenários de Salário |
| EP-04 | Motor de Cálculo e Comparação de Cenários |
| EP-05 | Relatórios e Dashboard |
| EP-06 | Interface Web |
| EP-07 | Infraestrutura e Qualidade (RNFs) |

---

## Tabela de Backlog

| ID | Backlog |
|---|---|
| EP-01 / US-01 | Cadastrar usuário |
| EP-01 / US-02 | Login e logout |
| EP-01 / US-03 | Isolar dados por usuário |
| EP-01 / US-04 | Alterar senha e dados do perfil |
| EP-02 / US-05 | Gerenciar categorias de gasto |
| EP-02 / US-06 | Criar mês de referência |
| EP-02 / US-07 | Lançar gasto no mês |
| EP-02 / US-07b | Cadastrar gastos fixos/recorrentes |
| EP-02 / US-08 | Editar e excluir gasto |
| EP-02 / US-09 | Criar mês a partir do anterior |
| EP-02 / US-10 | Registrar compras parceladas |
| EP-02 / US-10b | Definir orçamento por categoria |
| EP-03 / US-11 | Criar cenário de ganho |
| EP-03 / US-12 | Informar salário líquido direto |
| EP-03 / US-13 | Calcular líquido CLT a partir do bruto |
| EP-03 / US-13b | Calcular líquido PJ a partir do faturamento |
| EP-03 / US-14 | Adicionar rendas extras ao cenário |
| EP-03 / US-15 | Manter tabelas de INSS/IRRF por ano |
| EP-03 / US-16 | Marcar cenário principal |
| EP-03 / US-16b | Considerar 13º e férias na visão anual |
| EP-04 / US-17 | Calcular saldo do cenário vs. gastos do mês |
| EP-04 / US-18 | Comparar cenários lado a lado |
| EP-04 / US-19 | Calcular peso de cada categoria na renda |
| EP-04 / US-20 | Projetar 12 meses por cenário |
| EP-04 / US-21 | Recalcular automaticamente após alterações |
| EP-05 / US-22 | Resumo do mês |
| EP-05 / US-23 | Evolução mensal (histórico) |
| EP-05 / US-24 | Gráficos por categoria |
| EP-05 / US-25 | Exportar dados em CSV |
| EP-06 / US-26 | Telas de login e cadastro |
| EP-06 / US-27 | Tela do mês (lançamentos) |
| EP-06 / US-28 | Tela de cenários de ganho |
| EP-06 / US-29 | Tela de comparação de cenários |
| EP-06 / US-30 | Dashboard |
| EP-07 / RNF-01 | Execução local com um comando (Docker) |
| EP-07 / RNF-02 | Segurança e autenticação |
| EP-07 / RNF-03 | Precisão monetária |
| EP-07 / RNF-04 | Usabilidade e localização pt-BR |
| EP-07 / RNF-05 | Testabilidade |
| EP-07 / RNF-06 | Backup e restauração dos dados locais |
| EP-07 / RNF-07 | Observabilidade e logging |
| EP-07 / RNF-08 | Preparação para deploy em nuvem |
| EP-07 / RNF-09 | Modo de uso local |

---

## EP-01 — Autenticação e Usuários

| ID | User Story | Critérios de Aceitação | Pts | Prioridade |
|---|---|---|---|---|
| 01 | **Como** novo usuário, **quero** criar uma conta com nome, e-mail e senha, **para** ter meu próprio espaço no sistema. | ☐ É possível informar nome, e-mail e senha.<br>☐ O e-mail é único; e-mails duplicados são rejeitados com mensagem clara.<br>☐ A senha exige tamanho mínimo e é validada (confirmação de senha igual).<br>☐ A senha é armazenada com hash, nunca em texto puro.<br>☐ Ao criar a conta, as categorias padrão são geradas para o usuário (ver US-05). *(Movido para a US-05 na clarificação da spec 002-cadastro-usuario.)* | 3 | Alta |
| 02 | **Como** usuário, **quero** fazer login e logout, **para** que o sistema saiba quem está acessando. | ☐ Login com e-mail e senha retorna um token/sessão válido.<br>☐ Credenciais inválidas exibem mensagem genérica (sem revelar se o e-mail existe).<br>☐ O token expira após um período definido e pode ser renovado.<br>☐ O logout invalida a sessão no frontend e redireciona para o login.<br>☐ Rotas protegidas redirecionam para o login quando não há sessão. | 5 | Alta |
| 03 | **Como** usuário, **quero** que meus dados fiquem isolados dos outros usuários, **para** preservar minha privacidade. | ☐ Todo registro (mês, gasto, categoria, cenário) pertence a um usuário.<br>☐ A API só lista e altera registros do usuário autenticado.<br>☐ Acessar o ID de um registro de outro usuário retorna 404 (não 403, para não vazar existência).<br>☐ Existem testes automatizados cobrindo o isolamento. | 5 | Alta |
| 04 | **Como** usuário, **quero** alterar minha senha e meus dados de perfil, **para** manter a conta atualizada. | ☐ É possível alterar nome e e-mail (mantendo a unicidade).<br>☐ A troca de senha exige a senha atual.<br>☐ Após trocar a senha, as sessões antigas são invalidadas.<br>☐ Sem servidor de e-mail, a redefinição de senha esquecida é feita pelo admin do Django (documentado). | 2 | Baixa |

---

## EP-02 — Categorias e Cadastro do Mês (Gastos)

| ID | User Story | Critérios de Aceitação | Pts | Prioridade |
|---|---|---|---|---|
| 05 | **Como** usuário, **quero** gerenciar categorias de gasto, **para** organizar meus lançamentos do meu jeito. | ☐ Categorias padrão são criadas no cadastro: Moradia, Alimentação, Transporte, Saúde, Lazer, Educação, Outros. Usuários cadastrados antes da US-05 também recebem as categorias padrão (origem: clarificação da spec 002-cadastro-usuario).<br>☐ É possível criar, renomear e excluir categorias (nome único por usuário).<br>☐ Cada categoria pode ter uma cor para os gráficos.<br>☐ Uma categoria com gastos vinculados não pode ser excluída sem escolher outra categoria para receber esses gastos. | 3 | Alta |
| 06 | **Como** usuário, **quero** criar um mês de referência (MM/AAAA), **para** agrupar os gastos daquele período. | ☐ É possível criar um mês informando mês e ano.<br>☐ Cada mês existe uma única vez por usuário; duplicados são rejeitados com mensagem clara.<br>☐ Os meses aparecem listados em ordem cronológica.<br>☐ Um mês pode ser marcado como "fechado", o que bloqueia edições acidentais. | 3 | Alta |
| 07 | **Como** usuário, **quero** lançar gastos no mês por categoria, **para** saber para onde meu dinheiro vai. | ☐ Um gasto tem descrição, valor, categoria, data e forma de pagamento (opcional: dinheiro, débito, crédito, Pix).<br>☐ Valores zerados, negativos ou não numéricos são bloqueados.<br>☐ A data precisa estar dentro do mês de referência.<br>☐ O gasto é persistido e o total do mês e da categoria é atualizado. | 5 | Alta |
| 07b | **Como** usuário, **quero** cadastrar gastos fixos (aluguel, internet, assinaturas), **para** não precisar lançá-los todo mês. | ☐ É possível marcar um gasto como recorrente, com dia de vencimento.<br>☐ Ao criar um novo mês, os gastos recorrentes ativos são gerados automaticamente.<br>☐ Um gasto recorrente pode ter data de fim ou ser desativado.<br>☐ Alterar o valor do recorrente afeta só os meses seguintes, nunca os já existentes. | 5 | Alta |
| 08 | **Como** usuário, **quero** editar e excluir gastos, **para** corrigir lançamentos errados. | ☐ É possível alterar todos os campos de um gasto.<br>☐ As validações da US-07 valem também na edição.<br>☐ Há confirmação antes de excluir.<br>☐ Meses fechados bloqueiam edição e exclusão até serem reabertos. | 2 | Alta |
| 09 | **Como** usuário, **quero** criar um mês copiando o anterior, **para** ganhar tempo quando os gastos se repetem. | ☐ Na criação do mês existe a opção "copiar do mês anterior".<br>☐ É possível escolher quais gastos copiar antes de confirmar.<br>☐ As datas copiadas são ajustadas para o novo mês (ex.: dia 31 vira o último dia de um mês de 30 dias).<br>☐ Gastos recorrentes (US-07b) não são duplicados. | 3 | Média |
| 10 | **Como** usuário, **quero** registrar compras parceladas, **para** ver o impacto delas nos meses seguintes. | ☐ É possível informar o valor total ou o valor da parcela, o número de parcelas e o mês da primeira parcela.<br>☐ As parcelas são distribuídas nos meses seguintes (os meses são criados se ainda não existirem).<br>☐ Cada parcela exibe a indicação "n/N".<br>☐ Arredondamentos de centavos ficam na última parcela, sem sobrar nem faltar dinheiro.<br>☐ Excluir a compra permite escolher entre remover todas as parcelas ou só as futuras. | 8 | Média |
| 10b | **Como** usuário, **quero** definir um orçamento (limite) por categoria, **para** ser alertado quando gastar demais. | ☐ É possível definir um limite mensal por categoria.<br>☐ O sistema mostra o consumido vs. o limite (valor e %).<br>☐ Um alerta visual aparece em 80% e em 100% do limite.<br>☐ O limite pode ser mantido de um mês para o outro ou ajustado por mês. | 5 | Média |

---

## EP-03 — Ganhos e Cenários de Salário

| ID | User Story | Critérios de Aceitação | Pts | Prioridade |
|---|---|---|---|---|
| 11 | **Como** usuário, **quero** criar cenários de ganho (ex.: "Atual", "Promoção", "Proposta PJ"), **para** simular diferentes situações de renda. | ☐ É possível criar, renomear, duplicar e excluir cenários.<br>☐ O nome do cenário é único por usuário.<br>☐ Cada cenário define o tipo de cálculo: líquido direto, CLT ou PJ.<br>☐ Os cenários não dependem de um mês específico: valem para qualquer mês cadastrado. | 3 | Alta |
| 12 | **Como** usuário, **quero** informar diretamente o valor líquido que recebo, **para** simular rápido sem entrar em detalhes de impostos. | ☐ É possível informar um valor líquido mensal.<br>☐ Valores negativos ou não numéricos são bloqueados.<br>☐ O valor informado é usado sem nenhum desconto adicional. | 2 | Alta |
| 13 | **Como** usuário, **quero** que o sistema calcule o líquido CLT a partir do bruto, **para** comparar propostas de forma realista. | ☐ Informo o salário bruto, o número de dependentes e descontos adicionais (VT, plano de saúde, pensão, outros).<br>☐ O INSS é calculado de forma progressiva por faixa, respeitando o teto.<br>☐ O IRRF é calculado sobre a base (bruto − INSS − dependentes − deduções legais), com a tabela vigente do ano (US-15).<br>☐ O resultado mostra o detalhamento: bruto, INSS, IRRF, outros descontos e líquido.<br>☐ O cálculo é validado contra ao menos 5 casos de teste conferidos manualmente. | 8 | Alta |
| 13b | **Como** usuário, **quero** que o sistema estime o líquido PJ a partir do faturamento, **para** comparar CLT vs. PJ. | ☐ Informo o faturamento mensal, a alíquota do imposto (ex.: Simples Nacional), o pró-labore e o custo do contador.<br>☐ O INSS sobre o pró-labore é descontado.<br>☐ O resultado mostra o detalhamento: faturamento, impostos, pró-labore/INSS, contador e líquido.<br>☐ A tela deixa claro que é uma estimativa simplificada. | 8 | Média |
| 14 | **Como** usuário, **quero** adicionar rendas extras a um cenário (freela, aluguel, VA/VR), **para** ter a renda total real. | ☐ É possível adicionar várias rendas extras com descrição e valor.<br>☐ Cada renda extra pode ser marcada como "entra no saldo" ou "benefício restrito" (ex.: VR só para alimentação).<br>☐ As rendas extras somam no total do cenário e aparecem separadas no detalhamento. | 3 | Média |
| 15 | **Como** usuário, **quero** que as tabelas de INSS e IRRF sejam configuráveis por ano, **para** que os cálculos continuem certos quando a lei mudar. | ☐ As faixas de INSS e IRRF ficam no banco, versionadas por ano de vigência.<br>☐ A tabela vigente vem pré-carregada (fixture/migration).<br>☐ Um admin pode cadastrar a tabela de um novo ano sem mexer em código.<br>☐ O cálculo usa a tabela do ano do mês de referência. | 5 | Alta |
| 16 | **Como** usuário, **quero** marcar um cenário como principal, **para** que ele seja o padrão nos resumos e no dashboard. | ☐ Só existe um cenário principal por usuário por vez.<br>☐ Marcar outro cenário como principal desmarca o anterior.<br>☐ Se o cenário principal for excluído, o sistema pede para escolher outro. | 2 | Média |
| 16b | **Como** usuário, **quero** que o 13º e as férias (+1/3) entrem na visão anual dos cenários CLT, **para** comparar com PJ de forma justa. | ☐ Na visão anual, os cenários CLT incluem o 13º e as férias + 1/3, com os descontos aplicáveis.<br>☐ É possível informar o FGTS como benefício (exibido à parte, fora do saldo disponível).<br>☐ A comparação CLT vs. PJ mostra o total anual e a média mensal equivalente. | 5 | Média |

---

## EP-04 — Motor de Cálculo e Comparação de Cenários

| ID | User Story | Critérios de Aceitação | Pts | Prioridade |
|---|---|---|---|---|
| 17 | **Como** usuário, **quero** ver o saldo de cada cenário contra os gastos do mês, **para** saber se sobra ou falta dinheiro. | ☐ Para cada cenário são calculados: renda líquida total, total de gastos, saldo (sobra/déficit) e % da renda comprometida.<br>☐ Déficits aparecem destacados.<br>☐ Benefícios restritos (US-14) só abatem gastos da categoria correspondente. | 5 | Alta |
| 18 | **Como** usuário, **quero** comparar vários cenários lado a lado no mesmo mês, **para** decidir qual situação é melhor. | ☐ É possível selecionar 2 ou mais cenários para comparar.<br>☐ A comparação mostra renda, gastos, saldo e % comprometida de cada cenário.<br>☐ As diferenças aparecem em termos práticos (ex.: "sobra R$ 850 a mais que o Atual").<br>☐ O melhor saldo fica destacado. | 5 | Alta |
| 19 | **Como** usuário, **quero** ver quanto cada categoria representa da renda em cada cenário, **para** identificar onde estou comprometido demais. | ☐ Para cada categoria é calculado o % sobre a renda de cada cenário.<br>☐ Categorias acima de um limite configurável (ex.: moradia > 30%) recebem alerta.<br>☐ Os percentuais somam o % total comprometido da US-17. | 3 | Média |
| 20 | **Como** usuário, **quero** projetar os próximos 12 meses para cada cenário, **para** planejar a longo prazo. | ☐ A projeção usa gastos recorrentes, parcelas futuras e a média dos gastos variáveis dos últimos meses.<br>☐ Para cada cenário são mostrados o saldo mês a mês e o saldo acumulado.<br>☐ Nos cenários CLT, o 13º e as férias entram nos meses configurados (US-16b).<br>☐ A projeção deixa claro quais valores são estimados. | 5 | Média |
| 21 | **Como** sistema, **quero** recalcular os resultados sempre que gastos ou cenários mudarem, **para** que os números nunca fiquem desatualizados. | ☐ Qualquer criação, edição ou exclusão de gasto ou cenário reflete nos resultados sem ação manual.<br>☐ Os cálculos são feitos sob demanda (ou com cache invalidado corretamente), sem resultados obsoletos.<br>☐ A lógica de cálculo fica isolada em uma camada de serviço testável, fora das views. | 3 | Alta |

---

## EP-05 — Relatórios e Dashboard

| ID | User Story | Critérios de Aceitação | Pts | Prioridade |
|---|---|---|---|---|
| 22 | **Como** usuário, **quero** um resumo do mês, **para** ver minha situação de relance. | ☐ O resumo exibe o total gasto, o total por categoria, o saldo do cenário principal e as maiores despesas.<br>☐ Mostra a variação em relação ao mês anterior (valor e %).<br>☐ Mostra os alertas de orçamento (US-10b). | 3 | Alta |
| 23 | **Como** usuário, **quero** ver a evolução dos meus gastos ao longo dos meses, **para** identificar tendências. | ☐ Um gráfico de linha/barras mostra o total gasto por mês.<br>☐ É possível filtrar por categoria e por período.<br>☐ A renda do cenário principal pode ser sobreposta ao gráfico. | 5 | Média |
| 24 | **Como** usuário, **quero** gráficos de distribuição por categoria, **para** entender a composição dos meus gastos. | ☐ Um gráfico de pizza/rosca mostra os gastos do mês por categoria.<br>☐ Um gráfico de barras compara as categorias entre meses.<br>☐ As cores seguem as cores das categorias (US-05).<br>☐ Os valores aparecem no tooltip em R$ e %. | 5 | Média |
| 25 | **Como** usuário, **quero** exportar meus dados em CSV, **para** analisar no Excel ou guardar como backup. | ☐ É possível exportar os gastos de um mês ou de um período.<br>☐ É possível exportar a comparação de cenários.<br>☐ O CSV abre corretamente no Excel pt-BR (separador `;`, vírgula decimal, UTF-8 com BOM). | 3 | Baixa |

---

## EP-06 — Interface Web

| ID | User Story | Critérios de Aceitação | Pts | Prioridade |
|---|---|---|---|---|
| 26 | **Como** usuário, **quero** telas de login e cadastro, **para** acessar o sistema pelo navegador. | ☐ Telas de login e cadastro cobrindo US-01 e US-02.<br>☐ Erros de validação aparecem ao lado de cada campo.<br>☐ A sessão persiste ao recarregar a página até o token expirar.<br>☐ O layout base da aplicação (menu, cabeçalho com usuário logado e logout) fica pronto. | 5 | Alta |
| 27 | **Como** usuário, **quero** uma tela do mês com os lançamentos, **para** cadastrar e revisar meus gastos. | ☐ Um seletor de mês permite criar novos meses (US-06, US-09).<br>☐ Uma tabela de gastos permite filtrar por categoria e ordenar por data e valor.<br>☐ Um formulário rápido cria e edita gastos (US-07, US-08), incluindo recorrentes e parcelados.<br>☐ Totais por categoria e o total do mês ficam visíveis na tela.<br>☐ Há feedback claro de sucesso e de erro nas operações. | 8 | Alta |
| 28 | **Como** usuário, **quero** uma tela de cenários de ganho, **para** criar e ajustar minhas simulações de salário. | ☐ CRUD de cenários (US-11).<br>☐ O formulário muda conforme o tipo: líquido direto, CLT ou PJ.<br>☐ O detalhamento do cálculo (bruto → descontos → líquido) aparece em tempo real enquanto os valores são digitados.<br>☐ Rendas extras podem ser adicionadas no próprio cenário. | 8 | Alta |
| 29 | **Como** usuário, **quero** uma tela de comparação de cenários, **para** visualizar qual situação me favorece. | ☐ É possível selecionar o mês e os cenários a comparar.<br>☐ Uma tabela lado a lado mostra os resultados da US-18.<br>☐ Um gráfico de barras compara renda vs. gastos vs. saldo por cenário.<br>☐ É possível alternar entre as visões mensal e anual (US-16b). | 8 | Alta |
| 30 | **Como** usuário, **quero** um dashboard inicial, **para** ter uma visão geral assim que entro no sistema. | ☐ O dashboard mostra o resumo do mês atual (US-22) e os gráficos das US-23 e US-24.<br>☐ Mostra um card com o saldo do cenário principal e atalhos para lançar gasto e comparar cenários.<br>☐ Um estado vazio orienta o usuário novo (ex.: "crie seu primeiro mês"). | 8 | Média |

---

## EP-07 — Infraestrutura e Qualidade (RNFs)

| ID | User Story | Critérios de Aceitação | Pts | Prioridade |
|---|---|---|---|---|
| RNF-01 | **Como** desenvolvedor, **quero** subir o sistema inteiro com um comando, **para** rodar localmente sem configuração manual. | ☑ `docker compose up` sobe `db` (PostgreSQL), `backend` (Django) e `frontend` (React).<br>☑ Os dados do banco persistem em um volume Docker entre reinicializações.<br>☑ As migrations rodam automaticamente na subida.<br>☑ Variáveis sensíveis ficam num `.env` (com `.env.example` versionado).<br>☑ O README documenta como subir, parar e acessar o sistema. | 5 | Alta |
| RNF-02 | **Como** usuário, **quero** que o sistema seja seguro, **para** proteger meus dados financeiros. | ☐ Senhas são armazenadas com hash (padrão do Django).<br>☐ A API exige autenticação em todas as rotas, exceto login e cadastro.<br>☑ O CORS é restrito à origem do frontend.<br>☑ Nenhum segredo fica versionado no repositório.<br>☐ Nenhum dado é enviado a serviços externos. | 5 | Alta |
| RNF-03 | **Como** usuário, **quero** que os valores sejam calculados com precisão, **para** não ter diferenças de centavos. | ☐ Valores monetários usam `DecimalField` no banco e `Decimal` no Python (nunca `float`).<br>☐ A regra de arredondamento é definida e documentada (ex.: ROUND_HALF_UP, 2 casas).<br>☐ O frontend não refaz cálculos financeiros: exibe os valores da API. | 3 | Alta |
| RNF-04 | **Como** usuário, **quero** uma interface clara e em português, **para** usar o sistema sem precisar de manual. | ☐ Valores em R$ (`R$ 1.234,56`) e datas em `dd/mm/aaaa`.<br>☐ O fluxo principal (cadastrar → criar mês → lançar gastos → criar cenário → comparar) é navegável sem instrução externa.<br>☐ As mensagens de erro são compreensíveis e dizem o que fazer.<br>☐ O layout funciona em desktop e celular. | 5 | Média |
| RNF-05 | **Como** desenvolvedor, **quero** testes automatizados, **para** evitar regressões, principalmente nos cálculos. | ☐ Os cálculos de INSS, IRRF, PJ, saldo e projeção têm testes unitários com casos conferidos manualmente.<br>☐ Os endpoints da API têm testes de integração, incluindo o isolamento entre usuários (US-03).<br>☐ É possível rodar toda a suíte com um comando (ex.: `docker compose run backend pytest`). | 8 | Alta |
| RNF-06 | **Como** usuário, **quero** fazer backup e restaurar meus dados, **para** não perder o histórico, já que o banco é local. | ☐ Um script/comando gera um dump do banco com data no nome do arquivo.<br>☐ Um script/comando restaura um dump.<br>☐ O procedimento está documentado no README. | 3 | Média |
| RNF-07 | **Como** desenvolvedor, **quero** logging estruturado, **para** depurar problemas. | ☐ Eventos-chave (login, erros, criação de mês, falhas de cálculo) são logados com timestamp.<br>☐ Os logs não contêm senhas nem tokens.<br>☐ Os logs podem ser consultados via `docker compose logs`. | 3 | Baixa |
| RNF-08 | **Como** desenvolvedor, **quero** que a arquitetura esteja pronta para ir para a nuvem, **para** hospedar o sistema no futuro sem retrabalho. | ☐ As configurações dependem só de variáveis de ambiente (12-factor).<br>☐ O frontend consome a API por uma URL configurável.<br>☐ (Backlog futuro — pós-entrega: frontend no Vercel, backend em Render/Railway, Postgres gerenciado como Neon/Supabase.) | 5 | Baixa |
| RNF-09 | **Como** usuário, **quero** um modo de uso separado do modo de desenvolvimento, **para** usar o sistema no dia a dia com meus dados reais de forma leve e sem expor detalhes técnicos na rede local. | ☐ Um comando documentado sobe o sistema no modo de uso, e outro no modo de desenvolvimento.<br>☐ No modo de uso, a interface é servida como build otimizado e a API roda em servidor de aplicação, sem recarga automática.<br>☐ No modo de uso, erros não exibem detalhes técnicos (stack traces, configurações) para nenhum dispositivo da rede.<br>☐ O modo de uso exige chave secreta própria e se recusa a subir com a chave padrão.<br>☐ Os dois modos usam o mesmo banco local, e trocar de modo não perde dados.<br>☐ Deve estar concluído antes de lançar dados financeiros reais (origem: clarificação da spec 001-infra-docker). | 5 | Alta |

---

## Backlog Futuro (pós-entrega)

| Item | Descrição |
|---|---|
| Pendências da spec 001 (RNF-01) | Validar o acesso pelo celular na rede local (SC-008: hoje fica carregando, suspeita de firewall ou isolamento no roteador), rodar o quickstart num host Linux (SC-007; hoje validado só no Windows, com containers Linux do Docker Desktop) e ter o README seguido por uma pessoa que não conhece o projeto (SC-006, na demo da Sprint 1). |
| Deploy em nuvem | Executar o RNF-08: frontend no Vercel, backend em serviço com container e Postgres gerenciado. |
| Importar extrato | Importar arquivos CSV/OFX do banco com sugestão automática de categoria. |
| Metas de economia | Definir metas (ex.: reserva de emergência) e acompanhar o progresso por cenário. |
| Cartão de crédito | Controlar a fatura (fechamento e vencimento) e o mês de competência vs. o mês de pagamento. |
| App mobile / PWA | Lançar gastos rapidamente pelo celular. |
