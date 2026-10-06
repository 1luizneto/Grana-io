import { useAuth } from '../../auth/AuthProvider.jsx'

// Página inicial provisória (FR-017). Os recursos financeiros entram nas próximas USs.
export default function Inicio() {
  const { usuario } = useAuth()

  return (
    <section>
      <h1>Início</h1>
      {usuario && <p>Olá, {usuario.nome}!</p>}
      <p>Os recursos financeiros chegam nas próximas entregas.</p>
    </section>
  )
}
