import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from './AuthProvider.jsx'

// Páginas que exigem sessão (FR-009; research R-05). Sem sessão, leva ao login guardando a página
// pedida, para voltar a ela depois de entrar.
export default function RotaProtegida({ children }) {
  const { estado } = useAuth()
  const local = useLocation()

  if (estado === 'verificando') return <p className="carregando">Carregando…</p>
  if (estado !== 'conectado') return <Navigate to="/entrar" replace state={{ de: local }} />
  return children ?? <Outlet />
}
