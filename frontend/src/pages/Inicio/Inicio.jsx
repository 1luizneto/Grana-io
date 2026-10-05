import { useAuth } from '../../auth/AuthProvider.jsx'
import { useSaudeApi } from '../../hooks/useSaudeApi.js'

const MENSAGENS = {
  carregando: 'Verificando a API…',
  ok: 'API acessível (banco operacional)',
  'banco-indisponivel': 'API acessível, banco indisponível',
  inacessivel: 'API inacessível',
}

// Página inicial provisória (FR-017). Os recursos financeiros entram nas próximas USs.
export default function Inicio() {
  const { usuario } = useAuth()
  const estado = useSaudeApi()

  return (
    <section>
      <h1>Início</h1>
      {usuario && <p>Olá, {usuario.nome}!</p>}
      <p>Os recursos financeiros chegam nas próximas entregas.</p>
      <p>{MENSAGENS[estado]}</p>
    </section>
  )
}
