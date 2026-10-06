// Cliente autenticado com renovação única (specs/005-telas-login-cadastro, research R-03).
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { lerSessao, salvarSessao } from '../auth/armazenamento.js'
import {
  _reiniciarParaTestes,
  registrarAoExpirar,
  requisitarAutenticada,
  SessaoExpirada,
} from './client.js'

const USUARIO = { nome: 'Ana Souza', email: 'ana@exemplo.com' }

function json(status, corpo) {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const VENCIDA = () => json(401, { code: 'token_not_valid', detail: 'Token expirado' })

function cabecalhoAutorizacao(chamada) {
  return chamada[1].headers.Authorization
}

function chamadasPara(fetch, trecho) {
  return fetch.mock.calls.filter(([url]) => url.includes(trecho))
}

let fetch

beforeEach(() => {
  _reiniciarParaTestes()
  salvarSessao({ acesso: 'acesso-velho', renovacao: 'renovacao-velha', usuario: USUARIO })
  fetch = vi.fn()
  vi.stubGlobal('fetch', fetch)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('requisitarAutenticada', () => {
  it('envia a credencial de acesso no cabeçalho Authorization', async () => {
    fetch.mockResolvedValue(json(200, { ok: true }))

    const resposta = await requisitarAutenticada('/usuarios/eu/')

    expect(resposta.status).toBe(200)
    expect(fetch.mock.calls[0][0]).toBe('/api/usuarios/eu/')
    expect(cabecalhoAutorizacao(fetch.mock.calls[0])).toBe('Bearer acesso-velho')
  })

  it('renova a credencial vencida, grava o par novo e repete a requisição', async () => {
    fetch.mockImplementation(async (url, opcoes) => {
      if (url.endsWith('/auth/renovar/')) {
        expect(JSON.parse(opcoes.body)).toEqual({ renovacao: 'renovacao-velha' })
        return json(200, { acesso: 'acesso-novo', renovacao: 'renovacao-nova' })
      }
      return opcoes.headers.Authorization === 'Bearer acesso-novo'
        ? json(200, { repetida: true })
        : VENCIDA()
    })

    const resposta = await requisitarAutenticada('/usuarios/eu/')

    expect(await resposta.json()).toEqual({ repetida: true })
    expect(lerSessao()).toEqual({ acesso: 'acesso-novo', renovacao: 'renovacao-nova', usuario: USUARIO })
  })

  it('renova uma única vez com 3 requisições simultâneas (uso único, spec 003)', async () => {
    let renovar
    fetch.mockImplementation((url, opcoes) => {
      if (url.endsWith('/auth/renovar/')) {
        return new Promise((resolve) => {
          renovar = () => resolve(json(200, { acesso: 'acesso-novo', renovacao: 'renovacao-nova' }))
        })
      }
      return Promise.resolve(
        opcoes.headers.Authorization === 'Bearer acesso-novo' ? json(200, {}) : VENCIDA(),
      )
    })

    const pendentes = [
      requisitarAutenticada('/a/'),
      requisitarAutenticada('/b/'),
      requisitarAutenticada('/c/'),
    ]
    await vi.waitFor(() => expect(renovar).toBeTypeOf('function'))
    renovar()
    const respostas = await Promise.all(pendentes)

    expect(respostas.map((r) => r.status)).toEqual([200, 200, 200])
    expect(chamadasPara(fetch, '/auth/renovar/')).toHaveLength(1)
    const repeticoes = fetch.mock.calls.filter(
      ([url, opcoes]) => !url.endsWith('/auth/renovar/') && cabecalhoAutorizacao([url, opcoes]) === 'Bearer acesso-novo',
    )
    expect(repeticoes).toHaveLength(3)
  })

  it('expira a sessão quando a renovação é recusada', async () => {
    const aoExpirar = vi.fn()
    registrarAoExpirar(aoExpirar)
    fetch.mockImplementation(async (url) =>
      url.endsWith('/auth/renovar/')
        ? json(401, { detail: 'Sessão expirada ou encerrada. Entre novamente.' })
        : VENCIDA(),
    )

    await expect(requisitarAutenticada('/usuarios/eu/')).rejects.toBeInstanceOf(SessaoExpirada)

    expect(lerSessao()).toBeNull()
    expect(aoExpirar).toHaveBeenCalledOnce()
  })

  it.each([
    ['401 sem code', { detail: 'As credenciais de autenticação não foram fornecidas.' }],
    ['conta desativada', { code: 'user_inactive', detail: 'Usuário está inativo' }],
  ])('expira a sessão sem tentar renovar (%s)', async (_caso, corpo) => {
    const aoExpirar = vi.fn()
    registrarAoExpirar(aoExpirar)
    fetch.mockResolvedValue(json(401, corpo))

    await expect(requisitarAutenticada('/usuarios/eu/')).rejects.toBeInstanceOf(SessaoExpirada)

    expect(chamadasPara(fetch, '/auth/renovar/')).toHaveLength(0)
    expect(lerSessao()).toBeNull()
    expect(aoExpirar).toHaveBeenCalledOnce()
  })

  it('sem sessão guardada, recusa sem chamar a API', async () => {
    localStorage.clear()

    await expect(requisitarAutenticada('/usuarios/eu/')).rejects.toBeInstanceOf(SessaoExpirada)

    expect(fetch).not.toHaveBeenCalled()
  })

  it('usa a credencial gravada por outra aba quando perde a corrida da renovação', async () => {
    const aoExpirar = vi.fn()
    registrarAoExpirar(aoExpirar)
    fetch.mockImplementation(async (url, opcoes) => {
      if (url.endsWith('/auth/renovar/')) {
        // Outra aba renovou primeiro: gravou o par novo, e a renovação desta aba é recusada.
        salvarSessao({ acesso: 'acesso-da-outra-aba', renovacao: 'renovacao-da-outra-aba', usuario: USUARIO })
        return json(401, { detail: 'Sessão expirada ou encerrada. Entre novamente.' })
      }
      return opcoes.headers.Authorization === 'Bearer acesso-da-outra-aba' ? json(200, {}) : VENCIDA()
    })

    const resposta = await requisitarAutenticada('/usuarios/eu/')

    expect(resposta.status).toBe(200)
    expect(lerSessao().renovacao).toBe('renovacao-da-outra-aba')
    expect(aoExpirar).not.toHaveBeenCalled()
  })
})
