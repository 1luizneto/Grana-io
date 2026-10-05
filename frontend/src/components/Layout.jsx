import { Outlet, useNavigate } from 'react-router'
import { useAuth } from '../auth/AuthProvider.jsx'

// Layout das páginas protegidas (FR-012): cabeçalho com o sistema, a pessoa conectada e "Sair".
export default function Layout() {
  const { usuario, sair } = useAuth()
  const navegar = useNavigate()

  async function aoSair() {
    await sair()
    navegar('/entrar', { replace: true })
  }

  return (
    <div className="aplicacao">
      <header className="cabecalho">
        <span className="marca">Grana.io</span>
        <span className="usuario">{usuario?.nome}</span>
        <button type="button" onClick={aoSair}>
          Sair
        </button>
      </header>
      <main className="conteudo">
        <Outlet />
      </main>
    </div>
  )
}
