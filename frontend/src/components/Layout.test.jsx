// Layout base das páginas protegidas (US4 e US5).
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route } from 'react-router'
import { describe, expect, it } from 'vitest'
import { lerSessao, salvarSessao } from '../auth/armazenamento.js'
import RotaProtegida from '../auth/RotaProtegida.jsx'
import RotaPublica from '../auth/RotaPublica.jsx'
import Entrar from '../pages/Entrar/Entrar.jsx'
import { renderizarComRotas } from '../testes/renderizar.jsx'
import { json, LOGIN_OK, simularApi, USUARIO_ANA } from '../testes/respostas.js'
import Layout from './Layout.jsx'

const ROTAS = [
  <Route key="protegidas" element={<RotaProtegida />}>
    <Route element={<Layout />}>
      <Route path="/" element={<p>conteúdo do início</p>} />
    </Route>
  </Route>,
  <Route key="publicas" element={<RotaPublica />}>
    <Route path="/entrar" element={<Entrar />} />
  </Route>,
]

function abrirConectada(rotaSair = () => json(204)) {
  salvarSessao(LOGIN_OK)
  simularApi({ '/usuarios/eu/': () => json(200, USUARIO_ANA), '/auth/sair/': rotaSair })
  renderizarComRotas(ROTAS, { rota: '/' })
  return userEvent.setup()
}

describe('layout: cabeçalho e saída (US4)', () => {
  it('mostra "Grana.io", o nome da pessoa e o botão "Sair"', async () => {
    abrirConectada()

    const cabecalho = await screen.findByRole('banner')
    expect(cabecalho).toHaveTextContent('Grana.io')
    expect(cabecalho).toHaveTextContent('Ana Souza')
    expect(screen.getByRole('button', { name: 'Sair' })).toBeInTheDocument()
    expect(screen.getByText('conteúdo do início')).toBeInTheDocument()
  })

  it('"Sair" leva ao login com "Você saiu do sistema." e apaga a sessão', async () => {
    const pessoa = abrirConectada()

    await pessoa.click(await screen.findByRole('button', { name: 'Sair' }))

    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
    expect(screen.getByTestId('local-atual')).toHaveTextContent('/entrar')
    expect(await screen.findByRole('alert')).toHaveTextContent('Você saiu do sistema.')
    expect(screen.queryByText('conteúdo do início')).not.toBeInTheDocument()
    expect(lerSessao()).toBeNull()
  })

  it('sai mesmo com o servidor fora do ar', async () => {
    const pessoa = abrirConectada(() => {
      throw new TypeError('Failed to fetch')
    })

    await pessoa.click(await screen.findByRole('button', { name: 'Sair' }))

    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
    expect(lerSessao()).toBeNull()
  })
})
