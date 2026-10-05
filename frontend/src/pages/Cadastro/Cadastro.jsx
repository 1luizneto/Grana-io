import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { useAuth } from '../../auth/AuthProvider.jsx'
import AvisoFormulario from '../../components/AvisoFormulario.jsx'
import CampoTexto from '../../components/CampoTexto.jsx'

const SEM_ERROS = { campos: {}, geral: null }

// Tela de cadastro (US3; specs/005-telas-login-cadastro/contracts/interface.md).
export default function Cadastro() {
  const { cadastrarEEntrar } = useAuth()
  const navegar = useNavigate()
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [erro, setErro] = useState(SEM_ERROS)
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    if (enviando) return
    setEnviando(true)
    setErro(SEM_ERROS)
    const resultado = await cadastrarEEntrar({ nome, email, senha, confirmacao_senha: confirmacao })
    if (resultado.ok) {
      navegar('/', { replace: true })
      return
    }
    if (resultado.contaCriada) {
      navegar('/entrar', { replace: true, state: { email: resultado.email } })
      return
    }
    // Mantém nome e e-mail e apaga as senhas depois da recusa (FR-004).
    setErro(resultado.erro)
    setSenha('')
    setConfirmacao('')
    setEnviando(false)
  }

  return (
    <main className="pagina-acesso">
      <form className="cartao" onSubmit={aoEnviar} noValidate>
        <h1>Criar conta</h1>
        <AvisoFormulario mensagem={erro.geral} />
        <CampoTexto
          rotulo="Nome"
          nome="nome"
          valor={nome}
          aoMudar={setNome}
          erros={erro.campos.nome}
          autoComplete="name"
        />
        <CampoTexto
          rotulo="E-mail"
          nome="email"
          tipo="email"
          valor={email}
          aoMudar={setEmail}
          erros={erro.campos.email}
          autoComplete="email"
        />
        <CampoTexto
          rotulo="Senha"
          nome="senha"
          tipo="password"
          valor={senha}
          aoMudar={setSenha}
          erros={erro.campos.senha}
          autoComplete="new-password"
        />
        <CampoTexto
          rotulo="Confirme a senha"
          nome="confirmacao_senha"
          tipo="password"
          valor={confirmacao}
          aoMudar={setConfirmacao}
          erros={erro.campos.confirmacao_senha}
          autoComplete="new-password"
        />
        <button type="submit" disabled={enviando}>
          {enviando ? 'Criando conta…' : 'Criar conta'}
        </button>
        <p className="alternativa">
          <Link to="/entrar">Já tenho conta</Link>
        </p>
      </form>
    </main>
  )
}
