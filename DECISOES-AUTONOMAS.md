# Decisões tomadas em modo autônomo

Em 2026-11-13 o responsável pediu: "vai continuando o projeto até onde der, vai tomando as
decisões, faz um arquivo só com isso pra depois eu olhar". Este arquivo é esse registro.

**Como ler**: cada decisão diz o que foi escolhido, por quê e onde ficou. As marcadas com ⚠️ são
as que mais valem uma conferida, porque mudam comportamento visível ou escopo.

## Como o trabalho foi conduzido

- Mesmo fluxo de sempre (spec-kit: specify → clarify → plan → tasks → analyze → implement), com
  commit + push a cada checkpoint, mensagens em pt-BR e sem trailers de IA.
- **Sem paradas**: nas perguntas do clarify e nos achados do analyze, escolhi eu (normalmente a
  opção recomendada) e anotei aqui.
- **PR e merge continuam com você.** Como as specs dependem umas das outras, cada branch nova sai
  da anterior (branches empilhadas). **Ordem de merge** na tabela abaixo: abra os PRs nessa
  ordem; depois do merge de uma, o PR da seguinte mostra só as mudanças dela.

## Branches e ordem de merge

| Ordem | Branch | US | Situação |
|---|---|---|---|
| 1 | `007-mes-referencia` | US-06 | Pronta para PR na `main` (20/20 tarefas) |

---

## Spec 007 — Mês de referência (US-06)

O specify, o clarify, o plan e as Phases 1 a 6 foram feitos com você acompanhando. Em modo
autônomo, só a Phase 7 (Polish).

- **D-007-1**: no BACKLOG, os 4 critérios da US-06 ficaram ☑. O 4º ("fechado bloqueia edições")
  tem nota: hoje o fechado só impede excluir o mês; o bloqueio dos gastos chega com a US-07 e a
  US-08.
- **D-007-2**: a US-07 ganhou dois critérios herdados: "mês fechado não aceita novos gastos" e
  "mês com gastos não pode ser excluído".
