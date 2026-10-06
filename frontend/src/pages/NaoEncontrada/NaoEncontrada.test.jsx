// Página não encontrada (US5; FR-018).
import { screen } from '@testing-library/react'
import { Route } from 'react-router'
import { describe, expect, it } from 'vitest'
import { salvarSessao } from '../../auth/armazenamento.js'
import RotaProtegida from '../../auth/RotaProtegida.jsx'
import { renderizarComRotas } from '../../testes/renderizar.jsx'
import { json, LOGIN_OK, simularApi, USUARIO_ANA } from '../../testes/respostas.js'
import NaoEncontrada from './NaoEncontrada.jsx'

const ROTAS = [
  <Route key="protegidas" element={<RotaProtegida />}>
    <Route path="/" element={<p>início</p>} />
  </Route>,
  <Route key="nao-encontrada" path="*" element={<NaoEncontrada />} />,
]

function conferirPagina() {
  expect(screen.getByRole('heading', { name: 'Página não encontrada.' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Voltar ao início' })).toHaveAttribute('href', '/')
}

describe('página não encontrada', () => {
  it('aparece para um endereço inexistente sem sessão', () => {
    renderizarComRotas(ROTAS, { rota: '/nao-existe' })

    conferirPagina()
  })

  it('aparece para um endereço inexistente com sessão', async () => {
    salvarSessao(LOGIN_OK)
    simularApi({ '/usuarios/eu/': () => json(200, USUARIO_ANA) })

    renderizarComRotas(ROTAS, { rota: '/outra/coisa' })

    conferirPagina()
  })
})
