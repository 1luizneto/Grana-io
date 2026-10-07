// Seletor de cor por rádios (FR-013; specs/006-categorias-gasto, research R-09).
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import SeletorCor from './SeletorCor.jsx'

const CORES = [
  { codigo: 'azul', nome: 'Azul', hex: '#2563EB' },
  { codigo: 'laranja', nome: 'Laranja', hex: '#EA580C' },
  { codigo: 'verde', nome: 'Verde', hex: '#16A34A' },
]

describe('SeletorCor', () => {
  it('mostra um grupo "Cor" com um rádio por cor, com o nome da cor', () => {
    render(<SeletorCor cores={CORES} valor={null} aoMudar={() => {}} />)

    expect(screen.getByRole('group', { name: 'Cor' })).toBeInTheDocument()
    expect(screen.getAllByRole('radio')).toHaveLength(3)
    expect(screen.getByRole('radio', { name: 'Verde' })).not.toBeChecked()
  })

  it('marca a cor recebida em "valor"', () => {
    render(<SeletorCor cores={CORES} valor="azul" aoMudar={() => {}} />)

    expect(screen.getByRole('radio', { name: 'Azul' })).toBeChecked()
  })

  it('avisa a cor escolhida com o clique', async () => {
    const aoMudar = vi.fn()
    render(<SeletorCor cores={CORES} valor={null} aoMudar={aoMudar} />)

    await userEvent.click(screen.getByRole('radio', { name: 'Verde' }))

    expect(aoMudar).toHaveBeenCalledWith('verde')
  })

  it('troca de cor com as setas do teclado', async () => {
    const aoMudar = vi.fn()
    render(<SeletorCor cores={CORES} valor="azul" aoMudar={aoMudar} />)

    screen.getByRole('radio', { name: 'Azul' }).focus()
    await userEvent.keyboard('{ArrowRight}')

    expect(aoMudar).toHaveBeenCalledWith('laranja')
  })

  it('dois seletores na mesma tela não se misturam', () => {
    render(
      <>
        <SeletorCor cores={CORES} valor="azul" aoMudar={() => {}} />
        <SeletorCor cores={CORES} valor="verde" aoMudar={() => {}} />
      </>,
    )

    const marcados = screen.getAllByRole('radio').filter((radio) => radio.checked)
    expect(marcados.map((radio) => radio.value)).toEqual(['azul', 'verde'])
  })
})
