import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { useAuth } from '../../auth/AuthProvider.jsx'
import AvisoFormulario from '../../components/AvisoFormulario.jsx'
import CampoTexto from '../../components/CampoTexto.jsx'

const SEM_ERROS = { campos: {}, geral: null }

// Tela de login (US1; specs/005-telas-login-cadastro/contracts/interface.md).
export default function Entrar() {
  const { entrar } = useAuth()
  const navegar = useNavigate()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState(SEM_ERROS)
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    if (enviando) return
    setEnviando(true)
    setErro(SEM_ERROS)
    const resultado = await entrar(email, senha)
    if (resultado.ok) {
      navegar('/', { replace: true })
      return
    }
    // Mantém o e-mail e apaga a senha depois da recusa (FR-004).
    setErro(resultado.erro)
    setSenha('')
    setEnviando(false)
  }

  return (
    <main className="pagina-acesso">
      <form className="cartao" onSubmit={aoEnviar} noValidate>
        <h1>Entrar</h1>
        <AvisoFormulario mensagem={erro.geral} />
        <CampoTexto
          rotulo="E-mail"
          nome="email"
          tipo="email"
          valor={email}
          aoMudar={setEmail}
          erros={erro.campos.email}
          autoComplete="username"
        />
        <CampoTexto
          rotulo="Senha"
          nome="senha"
          tipo="password"
          valor={senha}
          aoMudar={setSenha}
          erros={erro.campos.senha}
          autoComplete="current-password"
        />
        <button type="submit" disabled={enviando}>
          {enviando ? 'Entrando…' : 'Entrar'}
        </button>
        <p className="alternativa">
          <Link to="/cadastro">Criar conta</Link>
        </p>
      </form>
    </main>
  )
}
