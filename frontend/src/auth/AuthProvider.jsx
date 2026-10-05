import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { registrarAoExpirar } from '../api/client.js'
import { interpretarErro } from '../api/erros.js'
import * as apiSessao from '../api/sessao.js'
import { lerSessao, salvarSessao } from './armazenamento.js'

// Sessão da interface (docs/arquitetura.md §3; specs/005-telas-login-cadastro, research R-04).
// Estados: 'verificando' | 'conectado' | 'desconectado'.
export const MENSAGEM_SESSAO_EXPIRADA = 'Sua sessão expirou. Entre novamente.'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [sessao, setSessao] = useState(() => lerSessao())
  const [estado, setEstado] = useState(() => (sessao ? 'conectado' : 'desconectado'))
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

  const valor = useMemo(
    () => ({ usuario: sessao?.usuario ?? null, estado, aviso, limparAviso, entrar }),
    [sessao, estado, aviso, limparAviso, entrar],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const contexto = useContext(AuthContext)
  if (!contexto) throw new Error('useAuth precisa estar dentro de <AuthProvider>.')
  return contexto
}
