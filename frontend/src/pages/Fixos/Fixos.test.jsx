// Tela de gastos fixos (US-07b; specs/010-gastos-fixos/contracts/tela-fixos.md).
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { salvarSessao } from '../../auth/armazenamento.js'
import { renderizarComRotas } from '../../testes/renderizar.jsx'
import { json, LOGIN_OK, simularApi, USUARIO_ANA } from '../../testes/respostas.js'
import Fixos from './Fixos.jsx'

const CATEGORIAS = [
  { id: 2, nome: 'Moradia', cor: 'azul' },
  { id: 4, nome: 'Lazer', cor: 'rosa' },
]
const FORMAS = [
  { codigo: 'dinheiro', nome: 'Dinheiro' },
  { codigo: 'pix', nome: 'Pix' },
]
const fixo = (id, descricao, valor, dia, categoria, inicio, fim = null, ativo = true) => ({
  id,
  descricao,
  valor,
  categoria,
  forma_pagamento: '',
  dia_vencimento: dia,
  inicio,
  fim,
  ativo,
})
const ALUGUEL = fixo(3, 'Aluguel', '1500.00', 5, 2, '2026-11')
const STREAMING = fixo(4, 'Streaming', '39.90', 12, 4, '2026-11', '2027-01', false)

function abrir(rotas = {}) {
  salvarSessao(LOGIN_OK)
  const fetch = simularApi({
    '/usuarios/eu/': () => json(200, USUARIO_ANA),
    '/categorias/cores/': () => json(200, []),
    '/categorias/': () => json(200, CATEGORIAS),
    '/gastos/formas-pagamento/': () => json(200, FORMAS),
    ...rotas,
    '/fixos/': rotas['/fixos/'] ?? (() => json(200, [ALUGUEL, STREAMING])),
  })
  renderizarComRotas([<Route key="f" path="/fixos" element={<Fixos />} />], { rota: '/fixos' })
  return { fetch, pessoa: userEvent.setup() }
}

const chamadas = (fetch, metodo, fim) =>
  fetch.mock.calls.filter(
    ([url, opcoes]) => (opcoes?.method ?? 'GET') === metodo && (!fim || url.endsWith(fim)),
  )
const corpo = (chamada) => JSON.parse(chamada[1].body)
const formulario = (nome = 'Novo gasto fixo') => screen.getByRole('form', { name: nome })

async function esperarSucesso(texto) {
  expect(await screen.findByText(texto)).toHaveAttribute('role', 'status')
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(2026, 9, 15, 12))
})

afterEach(() => {
  vi.useRealTimers()
})

describe('tela de gastos fixos', () => {
  it('carrega e lista os fixos', async () => {
    abrir()

    expect(screen.getByText('Carregando gastos fixos…')).toBeInTheDocument()
    const itens = await screen.findAllByRole('listitem')
    expect(itens[0]).toHaveTextContent('Aluguel')
    expect(itens[0]).toHaveTextContent('R$ 1.500,00')
    expect(itens[0]).toHaveTextContent('dia 5')
    expect(itens[0]).toHaveTextContent('Moradia')
    expect(itens[0]).toHaveTextContent('desde 11/2026')
    expect(itens[0]).not.toHaveTextContent('Inativo')
    expect(itens[1]).toHaveTextContent('de 11/2026 a 01/2027')
    expect(itens[1]).toHaveTextContent('Inativo')
  })

  it('lista vazia', async () => {
    abrir({ '/fixos/': () => json(200, []) })

    expect(
      await screen.findByText('Nenhum gasto fixo. Cadastre o primeiro acima.'),
    ).toBeInTheDocument()
  })

  it('cadastra um fixo', async () => {
    const { fetch, pessoa } = abrir({
      '/fixos/': (opcoes) =>
        opcoes?.method === 'POST' ? json(201, ALUGUEL) : json(200, []),
    })
    await screen.findByText('Nenhum gasto fixo. Cadastre o primeiro acima.')
    const form = formulario()

    expect(within(form).getByLabelText('Início')).toHaveValue('2026-10')
    await pessoa.type(within(form).getByLabelText('Descrição'), 'Aluguel')
    await pessoa.type(within(form).getByLabelText('Valor'), '1.500,00')
    await pessoa.type(within(form).getByLabelText('Dia de vencimento'), '5')
    await pessoa.selectOptions(within(form).getByRole('combobox', { name: 'Categoria' }), '2')
    await pessoa.click(within(form).getByRole('button', { name: 'Cadastrar' }))

    await esperarSucesso('Gasto fixo cadastrado.')
    expect(corpo(chamadas(fetch, 'POST', '/fixos/')[0])).toEqual({
      descricao: 'Aluguel',
      valor: '1500.00',
      dia_vencimento: 5,
      categoria: 2,
      forma_pagamento: '',
      inicio: '2026-10',
      fim: null,
    })
    expect(within(formulario()).getByLabelText('Descrição')).toHaveValue('')
  })

  it('envia o mês de fim quando informado', async () => {
    const { fetch, pessoa } = abrir({
      '/fixos/': (opcoes) =>
        opcoes?.method === 'POST' ? json(201, ALUGUEL) : json(200, []),
    })
    await screen.findByText('Nenhum gasto fixo. Cadastre o primeiro acima.')
    const form = formulario()

    fireEvent.change(within(form).getByLabelText('Fim (opcional)'), {
      target: { value: '2027-03' },
    })
    await pessoa.click(within(form).getByRole('button', { name: 'Cadastrar' }))

    await waitFor(() => expect(chamadas(fetch, 'POST', '/fixos/')).toHaveLength(1))
    expect(corpo(chamadas(fetch, 'POST', '/fixos/')[0]).fim).toBe('2027-03')
  })

  it('erro de campo fica ligado ao campo', async () => {
    const { pessoa } = abrir({
      '/fixos/': (opcoes) =>
        opcoes?.method === 'POST'
          ? json(400, { dia_vencimento: ['Informe um dia de 1 a 31.'] })
          : json(200, []),
    })
    await screen.findByText('Nenhum gasto fixo. Cadastre o primeiro acima.')

    await pessoa.click(within(formulario()).getByRole('button', { name: 'Cadastrar' }))

    await waitFor(() =>
      expect(within(formulario()).getByLabelText('Dia de vencimento')).toHaveAccessibleDescription(
        'Informe um dia de 1 a 31.',
      ),
    )
  })

  it('edita com PATCH e volta ao cadastro', async () => {
    const { fetch, pessoa } = abrir({ '/fixos/3/': () => json(200, ALUGUEL) })

    await pessoa.click(await screen.findByRole('button', { name: 'Editar Aluguel' }))
    const form = formulario('Editar gasto fixo')
    expect(within(form).getByLabelText('Valor')).toHaveValue('1500,00')
    expect(within(form).getByLabelText('Dia de vencimento')).toHaveValue(5)
    expect(within(form).getByLabelText('Início')).toHaveValue('2026-11')
    await pessoa.clear(within(form).getByLabelText('Valor'))
    await pessoa.type(within(form).getByLabelText('Valor'), '1600,00')
    await pessoa.click(within(form).getByRole('button', { name: 'Salvar alterações' }))

    await esperarSucesso('Gasto fixo atualizado.')
    expect(corpo(chamadas(fetch, 'PATCH', '/fixos/3/')[0])).toMatchObject({
      valor: '1600.00',
      inicio: '2026-11',
      fim: null,
    })
    expect(screen.getByRole('form', { name: 'Novo gasto fixo' })).toBeInTheDocument()
  })

  it('"Cancelar edição" volta sem chamar a API', async () => {
    const { fetch, pessoa } = abrir()

    await pessoa.click(await screen.findByRole('button', { name: 'Editar Aluguel' }))
    await pessoa.click(screen.getByRole('button', { name: 'Cancelar edição' }))

    expect(formulario()).toBeInTheDocument()
    expect(chamadas(fetch, 'PATCH')).toHaveLength(0)
  })

  it('desativa e reativa', async () => {
    const { fetch, pessoa } = abrir({
      '/fixos/3/': () => json(200, { ...ALUGUEL, ativo: false }),
      '/fixos/4/': () => json(200, { ...STREAMING, ativo: true }),
    })

    await pessoa.click(await screen.findByRole('button', { name: 'Desativar Aluguel' }))
    await esperarSucesso('Gasto fixo desativado.')
    expect(corpo(chamadas(fetch, 'PATCH', '/fixos/3/')[0])).toEqual({ ativo: false })

    await pessoa.click(screen.getByRole('button', { name: 'Reativar Streaming' }))
    await esperarSucesso('Gasto fixo reativado.')
    expect(corpo(chamadas(fetch, 'PATCH', '/fixos/4/')[0])).toEqual({ ativo: true })
  })

  it('exclui com confirmação', async () => {
    const confirmar = vi
      .spyOn(window, 'confirm')
      .mockReturnValueOnce(false)
      .mockReturnValueOnce(true)
    const { fetch, pessoa } = abrir({ '/fixos/3/': () => json(204) })

    await pessoa.click(await screen.findByRole('button', { name: 'Excluir Aluguel' }))
    expect(confirmar).toHaveBeenCalledWith(
      'Excluir o gasto fixo "Aluguel"? Os gastos já lançados continuam.',
    )
    expect(chamadas(fetch, 'DELETE')).toHaveLength(0)

    await pessoa.click(screen.getByRole('button', { name: 'Excluir Aluguel' }))

    await esperarSucesso('Gasto fixo excluído.')
    expect(chamadas(fetch, 'DELETE', '/fixos/3/')).toHaveLength(1)
    confirmar.mockRestore()
  })
})
