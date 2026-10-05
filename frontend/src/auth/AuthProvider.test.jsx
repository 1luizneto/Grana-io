// Sessão da interface (specs/005-telas-login-cadastro, research R-04).
import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { json, LOGIN_OK, simularApi, USUARIO_ANA } from '../testes/respostas.js'
import { lerSessao } from './armazenamento.js'
import { AuthProvider, useAuth } from './AuthProvider.jsx'

function montar() {
  return renderHook(() => useAuth(), { wrapper: AuthProvider })
}

describe('AuthProvider: entrar (US1)', () => {
  it('grava a sessão e fica conectado com login aceito', async () => {
    const fetch = simularApi({ '/auth/entrar/': () => json(200, LOGIN_OK) })
    const { result } = montar()
    expect(result.current.estado).toBe('desconectado')

    let resultado
    await act(async () => {
      resultado = await result.current.entrar('ana@exemplo.com', 'uma-senha-boa-2026')
    })

    expect(resultado).toEqual({ ok: true })
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
      email: 'ana@exemplo.com',
      senha: 'uma-senha-boa-2026',
    })
    expect(result.current.estado).toBe('conectado')
    expect(result.current.usuario).toEqual(USUARIO_ANA)
    expect(lerSessao()).toEqual(LOGIN_OK)
    expect(localStorage.getItem('grana.sessao')).not.toContain('uma-senha-boa-2026')
  })

  it('devolve a mensagem genérica e não grava nada com login recusado', async () => {
    simularApi({ '/auth/entrar/': () => json(401, { detail: 'E-mail ou senha incorretos.' }) })
    const { result } = montar()

    let resultado
    await act(async () => {
      resultado = await result.current.entrar('ana@exemplo.com', 'errada-123')
    })

    expect(resultado).toEqual({
      ok: false,
      erro: { campos: {}, geral: 'E-mail ou senha incorretos.' },
    })
    expect(result.current.estado).toBe('desconectado')
    expect(lerSessao()).toBeNull()
  })
})
