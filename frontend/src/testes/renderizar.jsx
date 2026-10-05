// Ajuda dos testes: monta as rotas informadas com roteador em memória e AuthProvider.
import { render } from '@testing-library/react'
import { MemoryRouter, Routes, useLocation } from 'react-router'
import { AuthProvider } from '../auth/AuthProvider.jsx'

export function renderizarComRotas(rotas, { rota = '/' } = {}) {
  return render(
    <MemoryRouter initialEntries={[rota]}>
      <AuthProvider>
        <Routes>{rotas}</Routes>
        <LocalAtual />
      </AuthProvider>
    </MemoryRouter>,
  )
}

// Mostra o caminho atual, para os testes conferirem redirecionamentos.
function LocalAtual() {
  const local = useLocation()
  return <output data-testid="local-atual">{local.pathname}</output>
}
