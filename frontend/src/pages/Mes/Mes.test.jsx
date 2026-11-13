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

const gasto = (id, descricao, valor, data, forma, categoria) => ({
  id,
  descricao,
  valor,
  data,
  forma_pagamento: forma,
  mes: 7,
  categoria,
})
const GASTOS = [
  gasto(41, 'Feira', '49.70', '2026-10-02', '', 3),
  gasto(42, 'Mercado', '150.30', '2026-10-05', 'pix', 3),
  gasto(43, 'Uber', '23.45', '2026-10-05', 'dinheiro', 5),
]
const TOTAIS = {
  total: '223.45',
  por_categoria: [
    { categoria: 3, nome: 'Alimentação', cor: 'laranja', total: '200.00', quantidade: 2 },
    { categoria: 5, nome: 'Transporte', cor: 'roxo', total: '23.45', quantidade: 1 },
  ],
}

// Rotas de outubro com os 3 gastos acima.
const COM_GASTOS = {
  '/gastos/?mes=7': () => json(200, GASTOS),
  '/meses/7/totais/': () => json(200, TOTAIS),
}

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

const formularioGasto = (nome = 'Lançar gasto') => screen.getByRole('form', { name: nome })
const linhasDaTabela = () => within(screen.getByRole('table')).getAllByRole('row').slice(1)
const textoDasLinhas = () =>
  linhasDaTabela().map((linha) =>
    within(linha)
      .getAllByRole('cell')
      .slice(0, 5)
      .map((celula) => celula.textContent),
  )

describe('tela do mês: lançar gastos e ver os totais (US2)', () => {
  it('mostra os totais como a API mandou', async () => {
    abrir({ rota: '/meses/7', rotas: COM_GASTOS })

    const totais = await screen.findByRole('region', { name: 'Totais' })
    expect(await within(totais).findByText('R$ 223,45')).toBeInTheDocument()
    expect(within(totais).getByText('Total do mês')).toBeInTheDocument()
    const itens = within(totais).getAllByRole('listitem')
    expect(itens[0]).toHaveTextContent('Alimentação')
    expect(itens[0]).toHaveTextContent('R$ 200,00')
    expect(itens[0]).toHaveTextContent('2 gastos')
    expect(itens[1]).toHaveTextContent('Transporte')
    expect(itens[1]).toHaveTextContent('1 gasto')
  })

  it('mostra a tabela formatada, na ordem da API', async () => {
    abrir({ rota: '/meses/7', rotas: COM_GASTOS })

    await screen.findByRole('table')
    expect(textoDasLinhas()).toEqual([
      ['02/10/2026', 'Feira', 'Alimentação', '—', 'R$ 49,70'],
      ['05/10/2026', 'Mercado', 'Alimentação', 'Pix', 'R$ 150,30'],
      ['05/10/2026', 'Uber', 'Transporte', 'Dinheiro', 'R$ 23,45'],
    ])
  })

  it('mês sem gastos: aviso e total zerado', async () => {
    abrir({ rota: '/meses/7' })

    expect(await screen.findByText('Nenhum gasto neste mês.')).toBeInTheDocument()
    const totais = screen.getByRole('region', { name: 'Totais' })
    expect(within(totais).getByText('R$ 0,00')).toBeInTheDocument()
  })

  it('lança um gasto, recarrega e deixa o formulário pronto para o próximo', async () => {
    const { fetch, pessoa } = abrir({
      rota: '/meses/7',
      rotas: { '/gastos/': () => json(201, { id: 44 }) },
    })
    await screen.findByText('Nenhum gasto neste mês.')
    const form = formularioGasto()
    const listasAntes = chamadas(fetch, 'GET', '/gastos/?mes=7').length

    await pessoa.type(within(form).getByLabelText('Descrição'), 'Mercado')
    await pessoa.type(within(form).getByLabelText('Valor'), '1.234,56')
    await pessoa.selectOptions(within(form).getByRole('combobox', { name: 'Categoria' }), '3')
    await pessoa.selectOptions(
      within(form).getByRole('combobox', { name: 'Forma de pagamento' }),
      'pix',
    )
    await pessoa.click(within(form).getByRole('button', { name: 'Lançar' }))

    await esperarSucesso('Gasto lançado.')
    expect(corpo(chamadas(fetch, 'POST', '/gastos/')[0])).toEqual({
      descricao: 'Mercado',
      valor: '1234.56',
      data: '2026-10-15',
      mes: 7,
      categoria: 3,
      forma_pagamento: 'pix',
    })
    expect(chamadas(fetch, 'GET', '/gastos/?mes=7').length).toBeGreaterThan(listasAntes)
    expect(within(form).getByLabelText('Descrição')).toHaveValue('')
    expect(within(form).getByLabelText('Valor')).toHaveValue('')
    expect(within(form).getByLabelText('Data')).toHaveValue('2026-10-15')
    expect(within(form).getByRole('combobox', { name: 'Categoria' })).toHaveValue('3')
    expect(within(form).getByRole('combobox', { name: 'Forma de pagamento' })).toHaveValue('')
    expect(within(form).getByLabelText('Descrição')).toHaveFocus()
  })

  it('desabilita o botão durante o envio', async () => {
    let responder
    const { pessoa } = abrir({
      rota: '/meses/7',
      rotas: {
        '/gastos/': () =>
          new Promise((resolver) => {
            responder = resolver
          }),
      },
    })
    await screen.findByText('Nenhum gasto neste mês.')

    await pessoa.click(within(formularioGasto()).getByRole('button', { name: 'Lançar' }))

    expect(within(formularioGasto()).getByRole('button', { name: 'Lançando…' })).toBeDisabled()
    responder(json(400, { descricao: ['Este campo é obrigatório.'] }))
    expect(
      await within(formularioGasto()).findByRole('button', { name: 'Lançar' }),
    ).toBeEnabled()
  })

  it('erro de campo: mensagem ligada ao campo e valores mantidos', async () => {
    const { pessoa } = abrir({
      rota: '/meses/7',
      rotas: { '/gastos/': () => json(400, { valor: ['Informe um valor maior que zero.'] }) },
    })
    await screen.findByText('Nenhum gasto neste mês.')
    const form = formularioGasto()

    await pessoa.type(within(form).getByLabelText('Descrição'), 'Mercado')
    await pessoa.type(within(form).getByLabelText('Valor'), '0')
    await pessoa.click(within(form).getByRole('button', { name: 'Lançar' }))

    const valor = within(form).getByLabelText('Valor')
    await waitFor(() =>
      expect(valor).toHaveAccessibleDescription('Informe um valor maior que zero.'),
    )
    expect(valor).toHaveValue('0')
    expect(within(form).getByLabelText('Descrição')).toHaveValue('Mercado')
  })

  it('erro geral da API vira alerta no formulário', async () => {
    const { pessoa } = abrir({
      rota: '/meses/7',
      rotas: {
        '/gastos/': () =>
          json(400, { detail: 'O mês 10/2026 está fechado. Reabra o mês para alterar os gastos.' }),
      },
    })
    await screen.findByText('Nenhum gasto neste mês.')

    await pessoa.click(within(formularioGasto()).getByRole('button', { name: 'Lançar' }))

    expect(await within(formularioGasto()).findByRole('alert')).toHaveTextContent(
      'O mês 10/2026 está fechado.',
    )
  })

  it('uma nova operação apaga a mensagem de sucesso anterior', async () => {
    let tentativa = 0
    const { pessoa } = abrir({
      rota: '/meses/7',
      rotas: {
        '/gastos/': () => {
          tentativa += 1
          return tentativa === 1
            ? json(201, { id: 44 })
            : json(400, { valor: ['Informe um valor maior que zero.'] })
        },
      },
    })
    await screen.findByText('Nenhum gasto neste mês.')
    const botao = () => within(formularioGasto()).getByRole('button', { name: 'Lançar' })

    await pessoa.click(botao())
    await esperarSucesso('Gasto lançado.')
    await pessoa.click(botao())

    await waitFor(() =>
      expect(within(formularioGasto()).getByLabelText('Valor')).toHaveAccessibleDescription(
        'Informe um valor maior que zero.',
      ),
    )
    expect(screen.queryByText('Gasto lançado.')).not.toBeInTheDocument()
  })

  it('a data padrão é hoje quando cai no mês; senão, o dia 1', async () => {
    abrir({ rota: '/meses/6' })

    const form = await screen.findByRole('form', { name: 'Lançar gasto' })
    expect(within(form).getByLabelText('Data')).toHaveValue('2026-09-01')
  })
})

describe('tela do mês: corrigir e excluir gastos (US3)', () => {
  it('"Editar" carrega o gasto no formulário e salva com PATCH', async () => {
    const { fetch, pessoa } = abrir({
      rota: '/meses/7',
      rotas: { ...COM_GASTOS, '/gastos/42/': () => json(200, GASTOS[1]) },
    })

    await pessoa.click(await screen.findByRole('button', { name: 'Editar Mercado' }))

    const form = formularioGasto('Editar gasto')
    expect(within(form).getByLabelText('Descrição')).toHaveValue('Mercado')
    expect(within(form).getByLabelText('Valor')).toHaveValue('150,30')
    expect(within(form).getByLabelText('Data')).toHaveValue('2026-10-05')
    expect(within(form).getByRole('combobox', { name: 'Categoria' })).toHaveValue('3')
    expect(within(form).getByRole('combobox', { name: 'Forma de pagamento' })).toHaveValue('pix')

    await pessoa.clear(within(form).getByLabelText('Valor'))
    await pessoa.type(within(form).getByLabelText('Valor'), '155,00')
    await pessoa.click(within(form).getByRole('button', { name: 'Salvar alterações' }))

    await esperarSucesso('Gasto atualizado.')
    const [patch] = chamadas(fetch, 'PATCH', '/gastos/42/')
    expect(corpo(patch)).toEqual({
      descricao: 'Mercado',
      valor: '155.00',
      data: '2026-10-05',
      mes: 7,
      categoria: 3,
      forma_pagamento: 'pix',
    })
    expect(await screen.findByRole('form', { name: 'Lançar gasto' })).toBeInTheDocument()
  })

  it('"Cancelar edição" volta a lançar sem chamar a API', async () => {
    const { fetch, pessoa } = abrir({ rota: '/meses/7', rotas: COM_GASTOS })

    await pessoa.click(await screen.findByRole('button', { name: 'Editar Mercado' }))
    await pessoa.click(screen.getByRole('button', { name: 'Cancelar edição' }))

    expect(screen.getByRole('form', { name: 'Lançar gasto' })).toBeInTheDocument()
    expect(within(formularioGasto()).getByLabelText('Descrição')).toHaveValue('')
    expect(chamadas(fetch, 'PATCH')).toHaveLength(0)
  })

  it('erro ao salvar a edição fica no formulário de edição', async () => {
    const { pessoa } = abrir({
      rota: '/meses/7',
      rotas: {
        ...COM_GASTOS,
        '/gastos/42/': () => json(400, { data: ['A data precisa estar dentro de 10/2026.'] }),
      },
    })

    await pessoa.click(await screen.findByRole('button', { name: 'Editar Mercado' }))
    await pessoa.click(screen.getByRole('button', { name: 'Salvar alterações' }))

    const form = formularioGasto('Editar gasto')
    await waitFor(() =>
      expect(within(form).getByLabelText('Data')).toHaveAccessibleDescription(
        'A data precisa estar dentro de 10/2026.',
      ),
    )
  })

  it('excluir pede confirmação e só exclui com "OK"', async () => {
    const confirmar = vi
      .spyOn(window, 'confirm')
      .mockReturnValueOnce(false)
      .mockReturnValueOnce(true)
    const { fetch, pessoa } = abrir({
      rota: '/meses/7',
      rotas: { ...COM_GASTOS, '/gastos/42/': () => json(204) },
    })

    await pessoa.click(await screen.findByRole('button', { name: 'Excluir Mercado' }))
    expect(confirmar).toHaveBeenCalledWith('Excluir o gasto "Mercado" de R$ 150,30?')
    expect(chamadas(fetch, 'DELETE')).toHaveLength(0)

    await pessoa.click(screen.getByRole('button', { name: 'Excluir Mercado' }))

    await esperarSucesso('Gasto excluído.')
    expect(chamadas(fetch, 'DELETE', '/gastos/42/')).toHaveLength(1)
    confirmar.mockRestore()
  })

  it('erro ao excluir vira alerta', async () => {
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(true)
    const { pessoa } = abrir({
      rota: '/meses/7',
      rotas: {
        ...COM_GASTOS,
        '/gastos/42/': () =>
          json(400, { detail: 'O mês 10/2026 está fechado. Reabra o mês para alterar os gastos.' }),
      },
    })

    await pessoa.click(await screen.findByRole('button', { name: 'Excluir Mercado' }))

    expect(await screen.findByText(/O mês 10\/2026 está fechado/)).toHaveAttribute('role', 'alert')
    confirmar.mockRestore()
  })
})

describe('tela do mês: fechar, reabrir e excluir o mês (US5)', () => {
  // Meses com estado: o PATCH muda o "fechado" que o GET seguinte devolve.
  function abrirComEstado(rotasExtras = {}) {
    let meses = MESES.map((mes) => ({ ...mes }))
    return abrir({
      rota: '/meses/7',
      rotas: {
        ...COM_GASTOS,
        '/meses/': () => json(200, meses),
        '/meses/7/': (opcoes) => {
          if (opcoes?.method === 'PATCH') {
            const { fechado } = JSON.parse(opcoes.body)
            meses = meses.map((mes) => (mes.id === 7 ? { ...mes, fechado } : mes))
            return json(200, meses.find((mes) => mes.id === 7))
          }
          meses = meses.filter((mes) => mes.id !== 7)
          return json(204)
        },
        ...rotasExtras,
      },
    })
  }

  it('fechar desabilita lançar, editar e excluir gastos; reabrir devolve', async () => {
    const { fetch, pessoa } = abrirComEstado()
    await screen.findByRole('table')

    await pessoa.click(screen.getByRole('button', { name: 'Fechar mês' }))

    await esperarSucesso('Mês fechado.')
    expect(corpo(chamadas(fetch, 'PATCH', '/meses/7/')[0])).toEqual({ fechado: true })
    expect(
      await screen.findByText('Mês fechado. Reabra o mês para lançar ou alterar gastos.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Fechado')).toBeInTheDocument()
    expect(within(formularioGasto()).getByLabelText('Descrição')).toBeDisabled()
    expect(screen.queryByRole('button', { name: 'Editar Mercado' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Excluir Mercado' })).not.toBeInTheDocument()

    await pessoa.click(screen.getByRole('button', { name: 'Reabrir mês' }))

    await esperarSucesso('Mês reaberto.')
    expect(corpo(chamadas(fetch, 'PATCH', '/meses/7/')[1])).toEqual({ fechado: false })
    expect(await screen.findByRole('button', { name: 'Editar Mercado' })).toBeInTheDocument()
    expect(within(formularioGasto()).getByLabelText('Descrição')).toBeEnabled()
  })

  it('excluir o mês pede confirmação e vai para outro mês', async () => {
    const confirmar = vi
      .spyOn(window, 'confirm')
      .mockReturnValueOnce(false)
      .mockReturnValueOnce(true)
    const { fetch, pessoa } = abrirComEstado()
    await screen.findByRole('table')

    await pessoa.click(screen.getByRole('button', { name: 'Excluir mês' }))
    expect(confirmar).toHaveBeenCalledWith('Excluir o mês 10/2026?')
    expect(chamadas(fetch, 'DELETE')).toHaveLength(0)

    await pessoa.click(screen.getByRole('button', { name: 'Excluir mês' }))

    await esperarSucesso('Mês excluído.')
    await waitFor(() => expect(local()).toHaveTextContent('/meses/6'))
    confirmar.mockRestore()
  })

  it('erro ao excluir o mês (com gastos) vira alerta', async () => {
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(true)
    const { pessoa } = abrirComEstado({
      '/meses/7/': () => json(400, { detail: 'Exclua ou mova os gastos antes de excluir o mês.' }),
    })
    await screen.findByRole('table')

    await pessoa.click(screen.getByRole('button', { name: 'Excluir mês' }))

    expect(
      await screen.findByText('Exclua ou mova os gastos antes de excluir o mês.'),
    ).toHaveAttribute('role', 'alert')
    expect(local()).toHaveTextContent('/meses/7')
    confirmar.mockRestore()
  })

  it('mês já fechado abre com o aviso e sem ações nos gastos', async () => {
    abrir({
      rota: '/meses/6',
      rotas: { '/gastos/?mes=6': () => json(200, [{ ...GASTOS[0], mes: 6, data: '2026-09-02' }]) },
    })

    expect(
      await screen.findByText('Mês fechado. Reabra o mês para lançar ou alterar gastos.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reabrir mês' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Editar Feira' })).not.toBeInTheDocument()
  })
})

describe('tela do mês: filtrar e ordenar (US4)', () => {
  const PARA_ORDENAR = [
    gasto(51, 'A', '999.99', '2026-10-01', '', 3),
    gasto(52, 'B', '1234.56', '2026-10-02', '', 5),
    gasto(53, 'C', '10.00', '2026-10-03', '', 3),
    gasto(54, 'D', '10.00', '2026-10-04', '', 5),
  ]
  const abrirParaOrdenar = (lista = PARA_ORDENAR) =>
    abrir({ rota: '/meses/7', rotas: { '/gastos/?mes=7': () => json(200, lista) } })
  const descricoes = () =>
    linhasDaTabela().map((linha) => within(linha).getAllByRole('cell')[1].textContent)
  const regiaoGastos = () => screen.getByRole('region', { name: 'Gastos' })

  it('filtra por categoria e volta a mostrar todas', async () => {
    const { pessoa } = abrirParaOrdenar()
    await screen.findByRole('table')
    const filtro = within(regiaoGastos()).getByRole('combobox', { name: 'Filtrar por categoria' })
    expect(within(filtro).getAllByRole('option').map((opcao) => opcao.textContent)).toEqual([
      'Todas as categorias',
      'Alimentação',
      'Transporte',
    ])

    await pessoa.selectOptions(filtro, '5')
    expect(descricoes()).toEqual(['B', 'D'])

    await pessoa.selectOptions(filtro, '')
    expect(descricoes()).toEqual(['A', 'B', 'C', 'D'])
  })

  it('filtro sem gastos: "Nenhum gasto nesta categoria."', async () => {
    const { pessoa } = abrirParaOrdenar([PARA_ORDENAR[0]])
    await screen.findByRole('table')

    await pessoa.selectOptions(
      within(regiaoGastos()).getByRole('combobox', { name: 'Filtrar por categoria' }),
      '5',
    )

    expect(screen.getByText('Nenhum gasto nesta categoria.')).toBeInTheDocument()
  })

  it.each([
    ['maior-valor', ['B', 'A', 'C', 'D']],
    ['menor-valor', ['C', 'D', 'A', 'B']],
    ['data-recente', ['D', 'C', 'B', 'A']],
    ['data-antiga', ['A', 'B', 'C', 'D']],
  ])('ordena por %s (empates na ordem da API)', async (ordem, esperado) => {
    const { pessoa } = abrirParaOrdenar()
    await screen.findByRole('table')
    const ordenar = within(regiaoGastos()).getByRole('combobox', { name: 'Ordenar por' })

    await pessoa.selectOptions(ordenar, ordem)

    expect(descricoes()).toEqual(esperado)
  })

  it('as opções de ordem têm nomes claros', async () => {
    abrirParaOrdenar()
    await screen.findByRole('table')
    const ordenar = within(regiaoGastos()).getByRole('combobox', { name: 'Ordenar por' })

    expect(within(ordenar).getAllByRole('option').map((opcao) => opcao.textContent)).toEqual([
      'Data (mais antigo)',
      'Data (mais recente)',
      'Maior valor',
      'Menor valor',
    ])
  })
})

describe('tela do mês: gastos fixos (spec 010)', () => {
  it('"Repetir todo mês" envia repetir e avisa que virou fixo', async () => {
    const { fetch, pessoa } = abrir({
      rota: '/meses/7',
      rotas: { '/gastos/': () => json(201, { id: 44, fixo: 9 }) },
    })
    await screen.findByText('Nenhum gasto neste mês.')
    const form = formularioGasto()

    await pessoa.type(within(form).getByLabelText('Descrição'), 'Internet')
    await pessoa.type(within(form).getByLabelText('Valor'), '99,90')
    await pessoa.selectOptions(within(form).getByRole('combobox', { name: 'Categoria' }), '3')
    await pessoa.click(within(form).getByRole('checkbox', { name: 'Repetir todo mês' }))
    await pessoa.click(within(form).getByRole('button', { name: 'Lançar' }))

    await esperarSucesso('Gasto lançado e cadastrado como fixo.')
    expect(corpo(chamadas(fetch, 'POST', '/gastos/')[0])).toMatchObject({
      descricao: 'Internet',
      repetir: true,
    })
    expect(within(form).getByRole('checkbox', { name: 'Repetir todo mês' })).not.toBeChecked()
  })

  it('a caixa não aparece ao editar', async () => {
    const { pessoa } = abrir({ rota: '/meses/7', rotas: COM_GASTOS })

    await pessoa.click(await screen.findByRole('button', { name: 'Editar Mercado' }))

    expect(
      within(formularioGasto('Editar gasto')).queryByRole('checkbox', { name: 'Repetir todo mês' }),
    ).not.toBeInTheDocument()
  })

  it('gasto gerado por um fixo tem a marca "fixo"', async () => {
    abrir({
      rota: '/meses/7',
      rotas: {
        '/gastos/?mes=7': () => json(200, [{ ...GASTOS[0], descricao: 'Aluguel', fixo: 9 }]),
        '/meses/7/totais/': () => json(200, TOTAIS),
      },
    })

    await screen.findByRole('table')
    const [linha] = linhasDaTabela()
    const descricao = within(linha).getAllByRole('cell')[1]
    expect(within(descricao).getByText('fixo')).toBeInTheDocument()
  })
})
