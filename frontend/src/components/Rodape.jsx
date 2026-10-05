import { useSaudeApi } from '../hooks/useSaudeApi.js'

const MENSAGENS = {
  carregando: 'Verificando a API…',
  ok: 'API acessível (banco operacional)',
  'banco-indisponivel': 'API acessível, banco indisponível',
  inacessivel: 'API inacessível',
}

// Estado da API em todas as telas, inclusive login e cadastro (spec 001; research R-09).
export default function Rodape() {
  const estado = useSaudeApi()
  return (
    <footer className="rodape">
      <span>Grana.io</span> · <span>{MENSAGENS[estado]}</span>
    </footer>
  )
}
