// Confere o próprio ambiente de teste (specs/005-telas-login-cadastro, T004).
import { describe, expect, it, vi } from 'vitest'

describe('ambiente de teste', () => {
  it('tem localStorage que grava e lê', () => {
    localStorage.setItem('chave', 'valor')
    expect(localStorage.getItem('chave')).toBe('valor')
  })

  it('tem AbortSignal.timeout, usado pelo cliente de API', () => {
    expect(typeof AbortSignal.timeout).toBe('function')
    expect(AbortSignal.timeout(1000)).toBeInstanceOf(AbortSignal)
  })

  it('permite substituir o fetch por um simulado', async () => {
    const simulado = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
    vi.stubGlobal('fetch', simulado)

    const resposta = await fetch('/api/qualquer/')

    expect(simulado).toHaveBeenCalledOnce()
    expect(resposta.status).toBe(200)
    vi.unstubAllGlobals()
  })
})
