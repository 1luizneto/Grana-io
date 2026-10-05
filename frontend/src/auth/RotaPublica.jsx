import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from './AuthProvider.jsx'

// Login e cadastro: quem já está conectado vai para a página pedida ou para o início (FR-010).
export default function RotaPublica({ children }) {
  const { estado } = useAuth()
  const local = useLocation()

  if (estado === 'verificando') return <p className="carregando">Carregando…</p>
  if (estado === 'conectado') {
    return <Navigate to={local.state?.de?.pathname ?? '/'} replace />
  }
  return children ?? <Outlet />
}
