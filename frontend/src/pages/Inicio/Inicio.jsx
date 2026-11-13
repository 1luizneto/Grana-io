import { Link } from 'react-router'
import { useAuth } from '../../auth/AuthProvider.jsx'

// Página inicial provisória (FR-017); o dashboard é a US-30.
export default function Inicio() {
  const { usuario } = useAuth()

  return (
    <section>
      <h1>Início</h1>
      {usuario && <p>Olá, {usuario.nome}!</p>}
      <p>
        Para lançar e revisar seus gastos, abra <Link to="/meses">Gastos do mês</Link>.
      </p>
    </section>
  )
}
