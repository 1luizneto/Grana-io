// Guardas de rota (US2; research R-05).
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route } from 'react-router'
import { describe, expect, it } from 'vitest'
import Entrar from '../pages/Entrar/Entrar.jsx'
import { renderizarComRotas } from '../testes/renderizar.jsx'
import { json, LOGIN_OK, simularApi, USUARIO_ANA } from '../testes/respostas.js'
import { salvarSessao } from './armazenamento.js'
import RotaProtegida from './RotaProtegida.jsx'
import RotaPublica from './RotaPublica.jsx'

const ROTAS = [
  <Route key="protegidas" element={<RotaProtegida />}>
    <Route path="/" element={<p>conteúdo protegido</p>} />
    <Route path="/algum-lugar-protegido" element={<p>lugar protegido</p>} />
  </Route>,
  <Route key="publicas" element={<RotaPublica />}>
    <Route path="/entrar" element={<Entrar />} />
    <Route path="/cadastro" element={<p>tela de cadastro</p>} />
  </Route>,
]

const local = () => screen.getByTestId('local-atual')

describe('rotas protegidas e públicas', () => {
  it('sem sessão, leva ao login e não mostra o conteúdo protegido', async () => {
    renderizarComRotas(ROTAS, { rota: '/' })

    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
    expect(local()).toHaveTextContent('/entrar')
    expect(screen.queryByText('conteúdo protegido')).not.toBeInTheDocument()
  })

  it('depois de entrar, volta para a página que a pessoa tentou abrir', async () => {
    simularApi({ '/auth/entrar/': () => json(200, LOGIN_OK) })
    renderizarComRotas(ROTAS, { rota: '/algum-lugar-protegido' })
    const pessoa = userEvent.setup()

    await pessoa.type(await screen.findByLabelText('E-mail'), 'ana@exemplo.com')
    await pessoa.type(screen.getByLabelText('Senha'), 'uma-senha-boa-2026{Enter}')

    expect(await screen.findByText('lugar protegido')).toBeInTheDocument()
    expect(local()).toHaveTextContent('/algum-lugar-protegido')
  })

  it.each(['/entrar', '/cadastro'])('com sessão, %s leva à página inicial', async (rota) => {
    salvarSessao(LOGIN_OK)
    simularApi({ '/usuarios/eu/': () => json(200, USUARIO_ANA) })

    renderizarComRotas(ROTAS, { rota })

    expect(await screen.findByText('conteúdo protegido')).toBeInTheDocument()
    expect(local()).toHaveTextContent(/^\/$/)
  })

  it('enquanto verifica a sessão, mostra "Carregando…" e nada protegido', async () => {
    salvarSessao(LOGIN_OK)
    simularApi({ '/usuarios/eu/': () => new Promise(() => {}) })

    renderizarComRotas(ROTAS, { rota: '/' })

    expect(screen.getByText('Carregando…')).toBeInTheDocument()
    expect(screen.queryByText('conteúdo protegido')).not.toBeInTheDocument()
  })
})
