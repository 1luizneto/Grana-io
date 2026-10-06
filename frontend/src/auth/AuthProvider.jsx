import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { registrarAoExpirar, SessaoExpirada } from '../api/client.js'
import { interpretarErro } from '../api/erros.js'
import * as apiSessao from '../api/sessao.js'
import * as apiUsuarios from '../api/usuarios.js'
import { apagarSessao, lerSessao, salvarSessao } from './armazenamento.js'

// Sessão da interface (docs/arquitetura.md §3; specs/005-telas-login-cadastro, research R-04).
// Estados: 'verificando' | 'conectado' | 'desconectado'.
export const MENSAGEM_SESSAO_EXPIRADA = 'Sua sessão expirou. Entre novamente.'
export const MENSAGEM_CONTA_CRIADA = 'Conta criada. Entre com sua senha.'
export const MENSAGEM_SAIU = 'Você saiu do sistema.'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [sessao, setSessao] = useState(() => lerSessao())
  // Com sessão guardada, começa verificando: nada protegido aparece antes da confirmação (SC-004).
  const [estado, setEstado] = useState(() => (sessao ? 'verificando' : 'desconectado'))
  // Aviso de uma vez só, mostrado pela tela de login (ex.: sessão expirada).
  const [aviso, setAviso] = useState(null)

  const desconectar = useCallback((mensagem) => {
    setSessao(null)
    setEstado('desconectado')
    setAviso(mensagem)
  }, [])

  // O cliente de API avisa aqui quando a sessão não pode mais ser renovada (FR-008).
  useEffect(
    () => registrarAoExpirar(() => desconectar(MENSAGEM_SESSAO_EXPIRADA)),
    [desconectar],
  )

  // Verificação ao abrir: renova a credencial se preciso, confirma a sessão e atualiza o nome.
  // No StrictMode o efeito roda duas vezes; a renovação única do cliente evita derrubar a sessão.
  useEffect(() => {
    if (!lerSessao()) return undefined
    let ativo = true
    apiSessao
      .obterEu()
      .then(async (resposta) => {
        if (!ativo) return
        const atual = lerSessao()
        if (resposta.ok && atual) {
          salvarSessao({ ...atual, usuario: await resposta.json() })
        }
        if (ativo && lerSessao()) {
          setSessao(lerSessao())
          setEstado('conectado')
        }
      })
      .catch((falha) => {
        // Sessão expirada já foi tratada pelo callback; queda momentânea do servidor mantém a
        // pessoa conectada com o nome guardado (research R-04).
        if (ativo && !(falha instanceof SessaoExpirada) && lerSessao()) setEstado('conectado')
      })
    return () => {
      ativo = false
    }
  }, [])

  const limparAviso = useCallback(() => setAviso(null), [])

  // Entra com e-mail e senha (US1). A senha só vai para a API; nunca é guardada (FR-016).
  const entrar = useCallback(async (email, senha) => {
    try {
      const resposta = await apiSessao.entrar(email, senha)
      if (!resposta.ok) return { ok: false, erro: await interpretarErro(resposta) }
      const { acesso, renovacao, usuario } = await resposta.json()
      salvarSessao({ acesso, renovacao, usuario })
      setSessao(lerSessao())
      setEstado('conectado')
      setAviso(null)
      return { ok: true }
    } catch (falha) {
      return { ok: false, erro: await interpretarErro(falha) }
    }
  }, [])

  // Cadastro seguido de entrada automática (US3; FR-019). Se só a entrada falhar, a tela leva ao
  // login com o e-mail preenchido e o aviso de conta criada.
  const cadastrarEEntrar = useCallback(
    async (dados) => {
      let conta
      try {
        const resposta = await apiUsuarios.cadastrar(dados)
        if (!resposta.ok) return { ok: false, erro: await interpretarErro(resposta) }
        conta = await resposta.json()
      } catch (falha) {
        return { ok: false, erro: await interpretarErro(falha) }
      }
      // A API devolve o e-mail normalizado (spec 002); é ele que entra no login.
      const login = await entrar(conta.email, dados.senha)
      if (login.ok) return { ok: true }
      setAviso(MENSAGEM_CONTA_CRIADA)
      return { ok: false, contaCriada: true, email: conta.email }
    },
    [entrar],
  )

  // Sair (US4; FR-011): encerra a sessão no servidor e sempre a descarta no navegador, mesmo se o
  // servidor não responder.
  const sair = useCallback(async () => {
    const atual = lerSessao()
    try {
      if (atual) await apiSessao.sair(atual.renovacao)
    } catch {
      // Falha de rede ou sessão já expirada: a saída local acontece do mesmo jeito.
    } finally {
      apagarSessao()
      desconectar(MENSAGEM_SAIU)
    }
  }, [desconectar])

  const valor = useMemo(
    () => ({
      usuario: sessao?.usuario ?? null,
      estado,
      aviso,
      limparAviso,
      entrar,
      cadastrarEEntrar,
      sair,
    }),
    [sessao, estado, aviso, limparAviso, entrar, cadastrarEEntrar, sair],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const contexto = useContext(AuthContext)
  if (!contexto) throw new Error('useAuth precisa estar dentro de <AuthProvider>.')
  return contexto
}
