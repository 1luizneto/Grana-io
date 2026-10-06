// Tela de login (US1; contracts/interface.md).
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route } from 'react-router'
import { describe, expect, it } from 'vitest'
import { renderizarComRotas } from '../../testes/renderizar.jsx'
import { json, LOGIN_OK, simularApi } from '../../testes/respostas.js'
import Entrar from './Entrar.jsx'

function abrirLogin() {
  renderizarComRotas(
    [
      <Route key="entrar" path="/entrar" element={<Entrar />} />,
      <Route key="inicio" path="/" element={<p>página inicial</p>} />,
    ],
    { rota: '/entrar' },
  )
  return userEvent.setup()
}

const email = () => screen.getByLabelText('E-mail')
const senha = () => screen.getByLabelText('Senha')
const botao = () => screen.getByRole('button', { name: /Entrar|Entrando/ })

describe('tela de login', () => {
  it('mostra "Este campo é obrigatório." abaixo de cada campo vazio', async () => {
    simularApi({
      '/auth/entrar/': () =>
        json(400, { email: ['Este campo é obrigatório.'], senha: ['Este campo é obrigatório.'] }),
    })
    const pessoa = abrirLogin()

    await pessoa.click(botao())

    expect(await screen.findAllByText('Este campo é obrigatório.')).toHaveLength(2)
    expect(email()).toHaveAttribute('aria-invalid', 'true')
    expect(email()).toHaveAccessibleDescription('Este campo é obrigatório.')
    expect(senha()).toHaveAccessibleDescription('Este campo é obrigatório.')
  })

  it('mostra a mensagem genérica, mantém o e-mail e apaga a senha', async () => {
    simularApi({ '/auth/entrar/': () => json(401, { detail: 'E-mail ou senha incorretos.' }) })
    const pessoa = abrirLogin()

    await pessoa.type(email(), 'ana@exemplo.com')
    await pessoa.type(senha(), 'senha-errada-1')
    await pessoa.click(botao())

    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha incorretos.')
    expect(email()).toHaveValue('ana@exemplo.com')
    expect(senha()).toHaveValue('')
  })

  it('mostra o aviso de muitas tentativas', async () => {
    simularApi({
      '/auth/entrar/': () =>
        json(429, { detail: 'Muitas tentativas. Tente novamente em instantes.' }),
    })
    const pessoa = abrirLogin()

    await pessoa.click(botao())

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Muitas tentativas. Tente novamente em instantes.',
    )
  })

  it('mostra a falha de comunicação e mantém o e-mail', async () => {
    simularApi({
      '/auth/entrar/': () => {
        throw new TypeError('Failed to fetch')
      },
    })
    const pessoa = abrirLogin()

    await pessoa.type(email(), 'ana@exemplo.com')
    await pessoa.click(botao())

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Não foi possível falar com o servidor. Tente novamente.',
    )
    expect(email()).toHaveValue('ana@exemplo.com')
  })

  it('trava o botão enquanto o login está em andamento', async () => {
    let responder
    simularApi({
      '/auth/entrar/': () =>
        new Promise((resolve) => {
          responder = () => resolve(json(401, { detail: 'E-mail ou senha incorretos.' }))
        }),
    })
    const pessoa = abrirLogin()

    await pessoa.click(botao())

    expect(botao()).toHaveTextContent('Entrando…')
    expect(botao()).toBeDisabled()
    responder()
    await waitFor(() => expect(botao()).toHaveTextContent('Entrar'))
    expect(botao()).toBeEnabled()
  })

  it('vai para a página inicial com o login aceito', async () => {
    simularApi({ '/auth/entrar/': () => json(200, LOGIN_OK) })
    const pessoa = abrirLogin()

    await pessoa.type(email(), 'ana@exemplo.com')
    await pessoa.type(senha(), 'uma-senha-boa-2026')
    await pessoa.click(botao())

    expect(await screen.findByText('página inicial')).toBeInTheDocument()
    expect(screen.getByTestId('local-atual')).toHaveTextContent('/')
  })

  it('envia o formulário com Enter no campo de senha', async () => {
    const fetch = simularApi({ '/auth/entrar/': () => json(200, LOGIN_OK) })
    const pessoa = abrirLogin()

    await pessoa.type(email(), 'ana@exemplo.com')
    await pessoa.type(senha(), 'uma-senha-boa-2026{Enter}')

    expect(await screen.findByText('página inicial')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledOnce()
  })
})

describe('tela de login: aviso pendente (US2)', () => {
  it('mostra "Sua sessão expirou. Entre novamente." quando a sessão expira', async () => {
    // Sessão guardada que não pode mais ser renovada: o provider expira e a tela de login avisa.
    localStorage.setItem(
      'grana.sessao',
      JSON.stringify({ ...LOGIN_OK, acesso: 'x', renovacao: 'x' }),
    )
    simularApi({
      '/usuarios/eu/': () => json(401, { code: 'token_not_valid', detail: 'Token inválido' }),
      '/auth/renovar/': () => json(401, { detail: 'Sessão expirada ou encerrada. Entre novamente.' }),
    })

    abrirLogin()

    expect(await screen.findByRole('alert')).toHaveTextContent('Sua sessão expirou. Entre novamente.')
    expect(screen.getAllByText('Sua sessão expirou. Entre novamente.')).toHaveLength(1)
  })
})
