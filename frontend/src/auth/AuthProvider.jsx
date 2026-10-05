import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { registrarAoExpirar } from '../api/client.js'
import { lerSessao } from './armazenamento.js'

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

  const valor = useMemo(
    () => ({ usuario: sessao?.usuario ?? null, estado, aviso, limparAviso }),
    [sessao, estado, aviso, limparAviso],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const contexto = useContext(AuthContext)
  if (!contexto) throw new Error('useAuth precisa estar dentro de <AuthProvider>.')
  return contexto
}
