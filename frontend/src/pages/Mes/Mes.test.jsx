// Tela do mês (US-27; specs/009-tela-mes/contracts/tela-mes.md).
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { salvarSessao } from '../../auth/armazenamento.js'
import { renderizarComRotas } from '../../testes/renderizar.jsx'
import { json, LOGIN_OK, simularApi, USUARIO_ANA } from '../../testes/respostas.js'
import Mes from './Mes.jsx'

const SETEMBRO = { id: 6, mes: 9, ano: 2026, rotulo: '09/2026', fechado: true }
const OUTUBRO = { id: 7, mes: 10, ano: 2026, rotulo: '10/2026', fechado: false }
const MESES = [SETEMBRO, OUTUBRO]

const CORES = [
  { codigo: 'laranja', nome: 'Laranja', hex: '#EA580C' },
  { codigo: 'roxo', nome: 'Roxo', hex: '#7C3AED' },
]
const CATEGORIAS = [
  { id: 3, nome: 'Alimentação', cor: 'laranja' },
  { id: 5, nome: 'Transporte', cor: 'roxo' },
]
const FORMAS = [
  { codigo: 'dinheiro', nome: 'Dinheiro' },
  { codigo: 'pix', nome: 'Pix' },
]
const SEM_TOTAIS = { total: '0.00', por_categoria: [] }

// Monta a tela com a API simulada. `rotas` acrescenta ou troca respostas (por fim do endereço).
function abrir({ rota = '/meses', meses = MESES, rotas = {} } = {}) {
  salvarSessao(LOGIN_OK)
  const fetch = simularApi({
    '/usuarios/eu/': () => json(200, USUARIO_ANA),
    '/categorias/cores/': () => json(200, CORES),
    '/categorias/': () => json(200, CATEGORIAS),
    '/gastos/formas-pagamento/': () => json(200, FORMAS),
    '/gastos/?mes=6': () => json(200, []),
    '/gastos/?mes=7': () => json(200, []),
    '/meses/6/totais/': () => json(200, SEM_TOTAIS),
    '/meses/7/totais/': () => json(200, SEM_TOTAIS),
    ...rotas,
    '/meses/': rotas['/meses/'] ?? (() => json(200, meses)),
  })
  renderizarComRotas(
    [
      <Route key="lista" path="/meses" element={<Mes />} />,
      <Route key="mes" path="/meses/:id" element={<Mes />} />,
    ],
    { rota },
  )
  return { fetch, pessoa: userEvent.setup() }
}

const local = () => screen.getByTestId('local-atual')
const chamadas = (fetch, metodo, fim) =>
  fetch.mock.calls.filter(
    ([url, opcoes]) => (opcoes?.method ?? 'GET') === metodo && (!fim || url.endsWith(fim)),
  )
const corpo = (chamada) => JSON.parse(chamada[1].body)

// Mensagem de sucesso: anunciada em role="status" (o <output> do auxiliar de rotas também é um
// "status", por isso a busca é pelo texto).
async function esperarSucesso(texto) {
  expect(await screen.findByText(texto)).toHaveAttribute('role', 'status')
}

beforeEach(() => {
  // Hoje: 15/10/2026. Só a data é simulada; os timers continuam reais (Testing Library).
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(2026, 9, 15, 12))
})

afterEach(() => {
  vi.useRealTimers()
})

describe('tela do mês: escolher e criar o mês (US1)', () => {
  it('abre no mês de hoje', async () => {
    abrir()

    await waitFor(() => expect(local()).toHaveTextContent('/meses/7'))
    expect(await screen.findByRole('heading', { name: '10/2026' })).toBeInTheDocument()
  })

  it('sem o mês de hoje, abre no mais recente', async () => {
    vi.setSystemTime(new Date(2026, 11, 3, 12))
    abrir()

    await waitFor(() => expect(local()).toHaveTextContent('/meses/7'))
  })

  it('sem meses, mostra o estado vazio e o formulário de novo mês', async () => {
    abrir({ meses: [] })

    expect(await screen.findByText('Nenhum mês criado. Crie o primeiro abaixo.')).toBeInTheDocument()
    expect(screen.getByRole('form', { name: 'Novo mês' })).toBeInTheDocument()
    expect(local()).toHaveTextContent('/meses')
  })

  it('mês fora da lista da pessoa: "Mês não encontrado."', async () => {
    abrir({ rota: '/meses/999' })

    expect(await screen.findByText('Mês não encontrado.')).toBeInTheDocument()
  })

  it('o seletor lista os meses (fechados indicados) e troca o endereço', async () => {
    const { pessoa } = abrir({ rota: '/meses/7' })

    const seletor = await screen.findByRole('combobox', { name: 'Escolher mês' })
    expect(within(seletor).getAllByRole('option').map((opcao) => opcao.textContent)).toEqual([
      '09/2026 (fechado)',
      '10/2026',
    ])
    expect(seletor).toHaveValue('7')

    await pessoa.selectOptions(seletor, '6')

    await waitFor(() => expect(local()).toHaveTextContent('/meses/6'))
    expect(await screen.findByRole('heading', { name: '09/2026' })).toBeInTheDocument()
  })

  it('o formulário de novo mês sugere o mês seguinte ao mais recente', async () => {
    abrir({ rota: '/meses/7' })

    const form = await screen.findByRole('form', { name: 'Novo mês' })
    expect(within(form).getByRole('combobox', { name: 'Mês' })).toHaveValue('11')
    expect(within(form).getByLabelText('Ano')).toHaveValue(2026)
  })

  it('sem meses, sugere o mês de hoje', async () => {
    abrir({ meses: [] })

    const form = await screen.findByRole('form', { name: 'Novo mês' })
    expect(within(form).getByRole('combobox', { name: 'Mês' })).toHaveValue('10')
  })

  it('cria um mês e vai para ele', async () => {
    let meses = MESES
    const novembro = { id: 8, mes: 11, ano: 2026, rotulo: '11/2026', fechado: false }
    const { fetch, pessoa } = abrir({
      rota: '/meses/7',
      rotas: {
        '/meses/': (opcoes) => {
          if (opcoes?.method === 'POST') {
            meses = [...MESES, novembro]
            return json(201, novembro)
          }
          return json(200, meses)
        },
        '/gastos/?mes=8': () => json(200, []),
        '/meses/8/totais/': () => json(200, SEM_TOTAIS),
      },
    })

    const form = await screen.findByRole('form', { name: 'Novo mês' })
    await pessoa.click(within(form).getByRole('button', { name: 'Criar mês' }))

    await esperarSucesso('Mês criado.')
    expect(corpo(chamadas(fetch, 'POST', '/meses/')[0])).toEqual({ mes: 11, ano: 2026 })
    await waitFor(() => expect(local()).toHaveTextContent('/meses/8'))
  })

  it('mês repetido: mostra a mensagem da API', async () => {
    const { pessoa } = abrir({
      rota: '/meses/7',
      rotas: {
        '/meses/': (opcoes) =>
          opcoes?.method === 'POST'
            ? json(400, { non_field_errors: ['Este mês já foi criado.'] })
            : json(200, MESES),
      },
    })

    const form = await screen.findByRole('form', { name: 'Novo mês' })
    await pessoa.selectOptions(within(form).getByRole('combobox', { name: 'Mês' }), '10')
    await pessoa.click(within(form).getByRole('button', { name: 'Criar mês' }))

    expect(await within(form).findByRole('alert')).toHaveTextContent('Este mês já foi criado.')
    expect(local()).toHaveTextContent('/meses/7')
  })
})
