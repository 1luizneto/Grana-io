import { describe, expect, it } from 'vitest'
import { interpretarErro, MENSAGEM_FALHA_COMUNICACAO } from './erros.js'

function resposta(status, corpo) {
  return new Response(typeof corpo === 'string' ? corpo : JSON.stringify(corpo), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('interpretarErro', () => {
  it('separa os erros de validação por campo (400)', async () => {
    const erro = await interpretarErro(resposta(400, { email: ['a'], senha: ['b', 'c'] }))

    expect(erro).toEqual({ campos: { email: ['a'], senha: ['b', 'c'] }, geral: null })
  })

  it('leva non_field_errors para a mensagem geral', async () => {
    const erro = await interpretarErro(
      resposta(400, { non_field_errors: ['Primeira.', 'Segunda.'], nome: ['x'] }),
    )

    expect(erro).toEqual({ campos: { nome: ['x'] }, geral: 'Primeira. Segunda.' })
  })

  it.each([
    [401, 'E-mail ou senha incorretos.'],
    [403, 'O cadastro de novas contas está desativado neste sistema.'],
    [429, 'Muitas tentativas. Tente novamente em instantes.'],
  ])('usa o detail como mensagem geral (%i)', async (status, detail) => {
    expect(await interpretarErro(resposta(status, { detail }))).toEqual({ campos: {}, geral: detail })
  })

  it.each([
    ['erro de rede', new TypeError('Failed to fetch')],
    ['tempo esgotado', new DOMException('Tempo esgotado', 'TimeoutError')],
    ['requisição abortada', new DOMException('Abortada', 'AbortError')],
  ])('mostra a falha de comunicação para %s', async (_caso, falha) => {
    expect(await interpretarErro(falha)).toEqual({ campos: {}, geral: MENSAGEM_FALHA_COMUNICACAO })
  })

  it.each([
    ['500', resposta(500, { detail: 'Erro interno' })],
    ['corpo que não é JSON', resposta(502, '<html>Bad Gateway</html>')],
  ])('mostra a falha de comunicação para resposta inesperada (%s)', async (_caso, r) => {
    expect(await interpretarErro(r)).toEqual({ campos: {}, geral: MENSAGEM_FALHA_COMUNICACAO })
  })

  it('tem o texto definido no contrato da interface', () => {
    expect(MENSAGEM_FALHA_COMUNICACAO).toBe('Não foi possível falar com o servidor. Tente novamente.')
  })
})
