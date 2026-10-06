import { describe, expect, it } from 'vitest'
import { apagarSessao, CHAVE_SESSAO, lerSessao, salvarSessao } from './armazenamento.js'

const SESSAO = {
  acesso: 'acesso-1',
  renovacao: 'renovacao-1',
  usuario: { nome: 'Ana Souza', email: 'ana@exemplo.com' },
}

describe('armazenamento da sessão', () => {
  it('grava na chave grana.sessao e lê o mesmo objeto', () => {
    salvarSessao(SESSAO)

    expect(CHAVE_SESSAO).toBe('grana.sessao')
    expect(JSON.parse(localStorage.getItem('grana.sessao'))).toEqual(SESSAO)
    expect(lerSessao()).toEqual(SESSAO)
  })

  it('apaga a sessão', () => {
    salvarSessao(SESSAO)

    apagarSessao()

    expect(localStorage.getItem('grana.sessao')).toBeNull()
    expect(lerSessao()).toBeNull()
  })

  it('devolve null sem nada guardado', () => {
    expect(lerSessao()).toBeNull()
  })

  it.each([
    ['JSON inválido', '{nao-e-json'],
    ['sem acesso', JSON.stringify({ ...SESSAO, acesso: '' })],
    ['sem renovação', JSON.stringify({ ...SESSAO, renovacao: undefined })],
    ['sem nome', JSON.stringify({ ...SESSAO, usuario: { email: 'ana@exemplo.com' } })],
    ['acesso que não é texto', JSON.stringify({ ...SESSAO, acesso: 123 })],
  ])('trata %s como sem sessão e apaga a chave', (_caso, bruto) => {
    localStorage.setItem('grana.sessao', bruto)

    expect(lerSessao()).toBeNull()
    expect(localStorage.getItem('grana.sessao')).toBeNull()
  })

  it('nunca guarda a senha nem campos extras (FR-016)', () => {
    salvarSessao({ ...SESSAO, senha: 'uma-senha-boa-2026', usuario: { ...SESSAO.usuario, senha: 'x' } })

    const bruto = localStorage.getItem('grana.sessao')
    expect(bruto).not.toContain('senha')
    expect(JSON.parse(bruto)).toEqual(SESSAO)
  })
})
