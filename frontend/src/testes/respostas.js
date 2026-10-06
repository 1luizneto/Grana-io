// Ajudas dos testes para simular respostas da API.
import { vi } from 'vitest'

export function json(status, corpo) {
  return new Response(corpo === undefined ? null : JSON.stringify(corpo), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

export const USUARIO_ANA = { nome: 'Ana Souza', email: 'ana@exemplo.com' }

export const LOGIN_OK = {
  acesso: 'acesso-1',
  renovacao: 'renovacao-1',
  usuario: USUARIO_ANA,
}

// Simula o fetch respondendo por rota: { '/auth/entrar/': () => json(200, ...) }.
export function simularApi(rotas) {
  const fetch = vi.fn(async (url, opcoes) => {
    const rota = Object.keys(rotas).find((caminho) => url.endsWith(caminho))
    if (!rota) throw new Error(`Rota não simulada: ${url}`)
    return rotas[rota](opcoes)
  })
  vi.stubGlobal('fetch', fetch)
  return fetch
}
