// Tela de categorias (US5; specs/006-categorias-gasto/contracts/tela-categorias.md).
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route } from 'react-router'
import { describe, expect, it, vi } from 'vitest'
import { salvarSessao } from '../../auth/armazenamento.js'
import { renderizarComRotas } from '../../testes/renderizar.jsx'
import { json, LOGIN_OK, simularApi, USUARIO_ANA } from '../../testes/respostas.js'
import Categorias from './Categorias.jsx'

const CORES = [
  { codigo: 'azul', nome: 'Azul', hex: '#2563EB' },
  { codigo: 'vermelho', nome: 'Vermelho', hex: '#DC2626' },
  { codigo: 'verde', nome: 'Verde', hex: '#16A34A' },
]

const LISTA = [
  { id: 1, nome: 'Moradia', cor: 'azul' },
  { id: 2, nome: 'Saúde', cor: 'vermelho' },
]

// Monta a tela com a API simulada. `rotas` acrescenta ou troca respostas (por fim do endereço).
function abrir(rotas = {}) {
  salvarSessao(LOGIN_OK)
  const fetch = simularApi({
    '/usuarios/eu/': () => json(200, USUARIO_ANA),
    '/categorias/cores/': () => json(200, CORES),
    ...rotas,
    '/categorias/': rotas['/categorias/'] ?? (() => json(200, LISTA)),
  })
  renderizarComRotas([<Route key="c" path="/categorias" element={<Categorias />} />], {
    rota: '/categorias',
  })
  return { fetch, pessoa: userEvent.setup() }
}

const formularioNovo = () => screen.getByRole('form', { name: 'Nova categoria' })
const chamadas = (fetch, metodo) =>
  fetch.mock.calls.filter(([, opcoes]) => (opcoes.method ?? 'GET') === metodo)

describe('tela de categorias', () => {
  it('carrega e lista as categorias na ordem da API, com a cor', async () => {
    abrir()

    expect(screen.getByText('Carregando categorias…')).toBeInTheDocument()
    const itens = await screen.findAllByRole('listitem')
    expect(itens.map((item) => within(item).getByText(/Moradia|Saúde/).textContent)).toEqual([
      'Moradia',
      'Saúde',
    ])
    expect(within(itens[1]).getByText('Cor: Vermelho')).toBeInTheDocument()
  })

  it('mostra o aviso de lista vazia', async () => {
    abrir({ '/categorias/': () => json(200, []) })

    expect(await screen.findByText('Nenhuma categoria. Crie a primeira acima.')).toBeInTheDocument()
  })

  it('cria uma categoria, recarrega a lista e limpa o formulário', async () => {
    let lista = LISTA
    const { fetch, pessoa } = abrir({
      '/categorias/': (opcoes) => {
        if (opcoes.method === 'POST') {
          lista = [...LISTA, { id: 3, nome: 'Pets', cor: 'verde' }]
          return json(201, { id: 3, nome: 'Pets', cor: 'verde' })
        }
        return json(200, lista)
      },
    })
    await screen.findAllByRole('listitem')

    const form = formularioNovo()
    await pessoa.type(within(form).getByLabelText('Nome'), 'Pets')
    await pessoa.click(within(form).getByRole('radio', { name: 'Verde' }))
    await pessoa.click(within(form).getByRole('button', { name: 'Adicionar' }))

    expect(await screen.findByText('Pets')).toBeInTheDocument()
    expect(JSON.parse(chamadas(fetch, 'POST')[0][1].body)).toEqual({ nome: 'Pets', cor: 'verde' })
    expect(within(form).getByLabelText('Nome')).toHaveValue('')
    expect(within(form).getByRole('radio', { name: 'Verde' })).not.toBeChecked()
  })

  it('sem cor escolhida, envia só o nome (a API escolhe a cor)', async () => {
    const { fetch, pessoa } = abrir({
      '/categorias/': (opcoes) =>
        opcoes.method === 'POST' ? json(201, { id: 3, nome: 'Pets', cor: 'verde' }) : json(200, LISTA),
    })
    await screen.findAllByRole('listitem')

    await pessoa.type(within(formularioNovo()).getByLabelText('Nome'), 'Pets{Enter}')

    await waitFor(() => expect(chamadas(fetch, 'POST')).toHaveLength(1))
    expect(JSON.parse(chamadas(fetch, 'POST')[0][1].body)).toEqual({ nome: 'Pets' })
  })

  it('trava o botão enquanto cria', async () => {
    let responder
    const { pessoa } = abrir({
      '/categorias/': (opcoes) =>
        opcoes.method === 'POST'
          ? new Promise((resolve) => {
              responder = () => resolve(json(201, { id: 3, nome: 'Pets', cor: 'azul' }))
            })
          : json(200, LISTA),
    })
    await screen.findAllByRole('listitem')

    const form = formularioNovo()
    await pessoa.type(within(form).getByLabelText('Nome'), 'Pets')
    await pessoa.click(within(form).getByRole('button', { name: 'Adicionar' }))

    expect(within(form).getByRole('button', { name: 'Adicionando…' })).toBeDisabled()
    responder()
    expect(await within(form).findByRole('button', { name: 'Adicionar' })).toBeEnabled()
  })

  it('mostra o erro da API ao lado do nome e mantém o texto', async () => {
    const { pessoa } = abrir({
      '/categorias/': (opcoes) =>
        opcoes.method === 'POST'
          ? json(400, { nome: ['Já existe uma categoria com este nome.'] })
          : json(200, LISTA),
    })
    await screen.findAllByRole('listitem')

    const nome = within(formularioNovo()).getByLabelText('Nome')
    await pessoa.type(nome, 'saúde{Enter}')

    await waitFor(() =>
      expect(nome).toHaveAccessibleDescription('Já existe uma categoria com este nome.'),
    )
    expect(nome).toHaveValue('saúde')
  })

  it('edita na própria linha e salva com PATCH', async () => {
    let lista = LISTA
    const { fetch, pessoa } = abrir({
      '/categorias/2/': () => {
        lista = [LISTA[0], { id: 2, nome: 'Saúde e bem-estar', cor: 'verde' }]
        return json(200, lista[1])
      },
      '/categorias/': () => json(200, lista),
    })

    await pessoa.click(await screen.findByRole('button', { name: 'Editar Saúde' }))
    const edicao = screen.getByRole('form', { name: 'Editar Saúde' })
    const nome = within(edicao).getByLabelText('Nome')
    await pessoa.clear(nome)
    await pessoa.type(nome, 'Saúde e bem-estar')
    await pessoa.click(within(edicao).getByRole('radio', { name: 'Verde' }))
    await pessoa.click(within(edicao).getByRole('button', { name: 'Salvar' }))

    expect(await screen.findByText('Saúde e bem-estar')).toBeInTheDocument()
    const patch = chamadas(fetch, 'PATCH')[0]
    expect(patch[0]).toBe('/api/categorias/2/')
    expect(JSON.parse(patch[1].body)).toEqual({ nome: 'Saúde e bem-estar', cor: 'verde' })
  })

  it('"Cancelar" desfaz a edição sem chamar a API', async () => {
    const { fetch, pessoa } = abrir()

    await pessoa.click(await screen.findByRole('button', { name: 'Editar Saúde' }))
    await pessoa.click(screen.getByRole('button', { name: 'Cancelar' }))

    expect(screen.getByRole('button', { name: 'Editar Saúde' })).toBeInTheDocument()
    expect(chamadas(fetch, 'PATCH')).toHaveLength(0)
  })

  it('pede confirmação antes de excluir e só exclui com "OK"', async () => {
    let lista = LISTA
    const { fetch, pessoa } = abrir({
      '/categorias/2/': () => {
        lista = [LISTA[0]]
        return json(204)
      },
      '/categorias/': () => json(200, lista),
    })
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValueOnce(false).mockReturnValueOnce(true)

    await pessoa.click(await screen.findByRole('button', { name: 'Excluir Saúde' }))
    expect(confirmar).toHaveBeenCalledWith('Excluir a categoria "Saúde"?')
    expect(chamadas(fetch, 'DELETE')).toHaveLength(0)

    await pessoa.click(screen.getByRole('button', { name: 'Excluir Saúde' }))
    await waitFor(() => expect(screen.queryByText('Saúde')).not.toBeInTheDocument())
    expect(chamadas(fetch, 'DELETE')[0][0]).toBe('/api/categorias/2/')
  })

  it('mostra a falha de comunicação ao carregar', async () => {
    abrir({
      '/categorias/': () => {
        throw new TypeError('Failed to fetch')
      },
    })

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Não foi possível falar com o servidor. Tente novamente.',
    )
  })
})
