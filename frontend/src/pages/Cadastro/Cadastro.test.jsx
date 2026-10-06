// Tela de cadastro (US3; contracts/interface.md).
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route } from 'react-router'
import { describe, expect, it } from 'vitest'
import RotaProtegida from '../../auth/RotaProtegida.jsx'
import RotaPublica from '../../auth/RotaPublica.jsx'
import { renderizarComRotas } from '../../testes/renderizar.jsx'
import { json, LOGIN_OK, simularApi, USUARIO_ANA } from '../../testes/respostas.js'
import Entrar from '../Entrar/Entrar.jsx'
import Cadastro from './Cadastro.jsx'

function abrirCadastro() {
  renderizarComRotas(
    [
      <Route key="protegidas" element={<RotaProtegida />}>
        <Route path="/" element={<p>página inicial</p>} />
      </Route>,
      <Route key="publicas" element={<RotaPublica />}>
        <Route path="/entrar" element={<Entrar />} />
        <Route path="/cadastro" element={<Cadastro />} />
      </Route>,
    ],
    { rota: '/cadastro' },
  )
  return userEvent.setup()
}

const campo = (rotulo) => screen.getByLabelText(rotulo)
const botao = () => screen.getByRole('button', { name: /Criar conta|Criando conta/ })

async function preencher(pessoa, { nome = 'Ana Souza', email = 'ana@exemplo.com' } = {}) {
  await pessoa.type(campo('Nome'), nome)
  await pessoa.type(campo('E-mail'), email)
  await pessoa.type(campo('Senha'), 'uma-senha-boa-2026')
  await pessoa.type(campo('Confirme a senha'), 'uma-senha-boa-2026')
}

describe('tela de cadastro', () => {
  it('mostra todos os erros de uma vez, cada um no seu campo, e apaga as senhas', async () => {
    simularApi({
      '/usuarios/': () =>
        json(400, {
          email: ['Já existe uma conta com este e-mail.'],
          senha: ['Esta senha é muito curta. Ela precisa conter pelo menos 8 caracteres.'],
          confirmacao_senha: ['As senhas não conferem.'],
        }),
    })
    const pessoa = abrirCadastro()

    await preencher(pessoa)
    await pessoa.click(botao())

    expect(await screen.findByText('Já existe uma conta com este e-mail.')).toBeInTheDocument()
    expect(campo('E-mail')).toHaveAccessibleDescription('Já existe uma conta com este e-mail.')
    expect(campo('Senha')).toHaveAccessibleDescription(
      'Esta senha é muito curta. Ela precisa conter pelo menos 8 caracteres.',
    )
    expect(campo('Confirme a senha')).toHaveAccessibleDescription('As senhas não conferem.')
    expect(campo('Nome')).toHaveValue('Ana Souza')
    expect(campo('E-mail')).toHaveValue('ana@exemplo.com')
    expect(campo('Senha')).toHaveValue('')
    expect(campo('Confirme a senha')).toHaveValue('')
  })

  it('mostra o aviso de cadastro fechado acima do formulário', async () => {
    simularApi({
      '/usuarios/': () =>
        json(403, { detail: 'O cadastro de novas contas está desativado neste sistema.' }),
    })
    const pessoa = abrirCadastro()

    await preencher(pessoa)
    await pessoa.click(botao())

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'O cadastro de novas contas está desativado neste sistema.',
    )
  })

  it('cria a conta, entra direto e vai para a página inicial', async () => {
    simularApi({
      '/usuarios/': () => json(201, USUARIO_ANA),
      '/auth/entrar/': () => json(200, LOGIN_OK),
    })
    const pessoa = abrirCadastro()

    await preencher(pessoa)
    await pessoa.click(botao())

    expect(await screen.findByText('página inicial')).toBeInTheDocument()
  })

  it('com a conta criada e o login falho, vai ao login com o e-mail e o aviso', async () => {
    simularApi({
      '/usuarios/': () => json(201, USUARIO_ANA),
      '/auth/entrar/': () => json(500, { detail: 'Erro interno' }),
    })
    const pessoa = abrirCadastro()

    await preencher(pessoa)
    await pessoa.click(botao())

    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
    expect(screen.getByTestId('local-atual')).toHaveTextContent('/entrar')
    expect(campo('E-mail')).toHaveValue('ana@exemplo.com')
    expect(await screen.findByRole('alert')).toHaveTextContent('Conta criada. Entre com sua senha.')
  })

  it('tem link para o login e trava o botão durante o envio', async () => {
    let responder
    simularApi({
      '/usuarios/': () =>
        new Promise((resolve) => {
          responder = () => resolve(json(400, { nome: ['Este campo é obrigatório.'] }))
        }),
    })
    const pessoa = abrirCadastro()

    expect(screen.getByRole('link', { name: 'Já tenho conta' })).toHaveAttribute('href', '/entrar')
    await pessoa.click(botao())
    expect(botao()).toHaveTextContent('Criando conta…')
    expect(botao()).toBeDisabled()
    responder()
    await waitFor(() => expect(botao()).toBeEnabled())
  })
})
