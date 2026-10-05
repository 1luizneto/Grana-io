// Sessão da interface (specs/005-telas-login-cadastro, research R-04).
import { act, renderHook, waitFor } from '@testing-library/react'
import { StrictMode } from 'react'
import { describe, expect, it } from 'vitest'
import { json, LOGIN_OK, simularApi, USUARIO_ANA } from '../testes/respostas.js'
import { lerSessao, salvarSessao } from './armazenamento.js'
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

describe('AuthProvider: verificação ao abrir (US2)', () => {
  const VENCIDA = () => json(401, { code: 'token_not_valid', detail: 'Token expirado' })

  it('com sessão guardada, verifica uma vez e atualiza o nome', async () => {
    salvarSessao(LOGIN_OK)
    const fetch = simularApi({
      '/usuarios/eu/': () => json(200, { nome: 'Ana S. Souza', email: 'ana@exemplo.com' }),
    })

    const { result } = montar()

    expect(result.current.estado).toBe('verificando')
    await waitFor(() => expect(result.current.estado).toBe('conectado'))
    expect(fetch).toHaveBeenCalledOnce()
    expect(result.current.usuario.nome).toBe('Ana S. Souza')
    expect(lerSessao().usuario.nome).toBe('Ana S. Souza')
  })

  it('em StrictMode, com o acesso vencido, renova uma única vez e continua conectado', async () => {
    salvarSessao(LOGIN_OK)
    const fetch = simularApi({
      '/auth/renovar/': () =>
        new Promise((resolve) =>
          setTimeout(() => resolve(json(200, { acesso: 'acesso-2', renovacao: 'renovacao-2' })), 10),
        ),
      '/usuarios/eu/': (opcoes) =>
        opcoes.headers.Authorization === 'Bearer acesso-2' ? json(200, USUARIO_ANA) : VENCIDA(),
    })

    const { result } = renderHook(() => useAuth(), {
      wrapper: ({ children }) => (
        <StrictMode>
          <AuthProvider>{children}</AuthProvider>
        </StrictMode>
      ),
    })

    await waitFor(() => expect(result.current.estado).toBe('conectado'))
    const renovacoes = fetch.mock.calls.filter(([url]) => url.endsWith('/auth/renovar/'))
    expect(renovacoes).toHaveLength(1)
    expect(lerSessao().renovacao).toBe('renovacao-2')
  })

  it('com a renovação recusada, desconecta e avisa que a sessão expirou', async () => {
    salvarSessao(LOGIN_OK)
    simularApi({
      '/auth/renovar/': () => json(401, { detail: 'Sessão expirada ou encerrada. Entre novamente.' }),
      '/usuarios/eu/': () => VENCIDA(),
    })

    const { result } = montar()

    await waitFor(() => expect(result.current.estado).toBe('desconectado'))
    expect(result.current.aviso).toBe('Sua sessão expirou. Entre novamente.')
    expect(lerSessao()).toBeNull()
  })

  it('sem sessão guardada, não chama a API', () => {
    const fetch = simularApi({})

    const { result } = montar()

    expect(result.current.estado).toBe('desconectado')
    expect(fetch).not.toHaveBeenCalled()
  })

  it('com falha de rede na verificação, mantém a sessão e fica conectado', async () => {
    salvarSessao(LOGIN_OK)
    simularApi({
      '/usuarios/eu/': () => {
        throw new TypeError('Failed to fetch')
      },
    })

    const { result } = montar()

    await waitFor(() => expect(result.current.estado).toBe('conectado'))
    expect(result.current.usuario).toEqual(USUARIO_ANA)
    expect(lerSessao()).toEqual(LOGIN_OK)
  })
})

describe('AuthProvider: cadastrar e entrar (US3)', () => {
  const DADOS = {
    nome: 'Ana Souza',
    email: ' Ana@Exemplo.com ',
    senha: 'uma-senha-boa-2026',
    confirmacao_senha: 'uma-senha-boa-2026',
  }

  async function cadastrar(result) {
    let resultado
    await act(async () => {
      resultado = await result.current.cadastrarEEntrar(DADOS)
    })
    return resultado
  }

  it('cria a conta e entra com o e-mail devolvido pela API', async () => {
    const fetch = simularApi({
      '/usuarios/': () => json(201, USUARIO_ANA),
      '/auth/entrar/': () => json(200, LOGIN_OK),
    })
    const { result } = montar()

    expect(await cadastrar(result)).toEqual({ ok: true })
    const login = fetch.mock.calls.find(([url]) => url.endsWith('/auth/entrar/'))
    expect(JSON.parse(login[1].body)).toEqual({ email: 'ana@exemplo.com', senha: 'uma-senha-boa-2026' })
    expect(result.current.estado).toBe('conectado')
    expect(lerSessao()).toEqual(LOGIN_OK)
  })

  it('devolve os erros por campo sem tentar entrar', async () => {
    const fetch = simularApi({
      '/usuarios/': () =>
        json(400, {
          email: ['Já existe uma conta com este e-mail.'],
          confirmacao_senha: ['As senhas não conferem.'],
        }),
    })
    const { result } = montar()

    expect(await cadastrar(result)).toEqual({
      ok: false,
      erro: {
        campos: {
          email: ['Já existe uma conta com este e-mail.'],
          confirmacao_senha: ['As senhas não conferem.'],
        },
        geral: null,
      },
    })
    expect(fetch).toHaveBeenCalledOnce()
    expect(result.current.estado).toBe('desconectado')
  })

  it('com a conta criada e o login falho, avisa e não grava nada', async () => {
    simularApi({
      '/usuarios/': () => json(201, USUARIO_ANA),
      '/auth/entrar/': () => json(500, { detail: 'Erro interno' }),
    })
    const { result } = montar()

    expect(await cadastrar(result)).toEqual({ ok: false, contaCriada: true, email: 'ana@exemplo.com' })
    expect(result.current.aviso).toBe('Conta criada. Entre com sua senha.')
    expect(lerSessao()).toBeNull()
  })
})
