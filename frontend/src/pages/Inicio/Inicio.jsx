import { useSaudeApi } from '../../hooks/useSaudeApi.js'

const MENSAGENS = {
  carregando: 'Verificando a API…',
  ok: 'API acessível (banco operacional)',
  'banco-indisponivel': 'API acessível, banco indisponível',
  inacessivel: 'API inacessível',
}

export default function Inicio() {
  const estado = useSaudeApi()

  return (
    <main>
      <h1>Grana.io</h1>
      <p>{MENSAGENS[estado]}</p>
    </main>
  )
}
