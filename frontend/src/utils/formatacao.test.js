// Formatação pt-BR sem cálculos (specs/009-tela-mes/research.md, R-03).
import { describe, expect, it } from 'vitest'
import {
  emCentavos,
  formatarData,
  formatarMoeda,
  paraValorDaApi,
  paraValorDigitado,
} from './formatacao.js'

describe('formatarMoeda', () => {
  it.each([
    ['0.00', 'R$ 0,00'],
    ['150.30', 'R$ 150,30'],
    ['1234.50', 'R$ 1.234,50'],
    ['1000000.00', 'R$ 1.000.000,00'],
    ['9999999999.99', 'R$ 9.999.999.999,99'],
    ['-5.00', '-R$ 5,00'],
  ])('%s → %s', (valor, esperado) => {
    expect(formatarMoeda(valor)).toBe(esperado)
  })
})

describe('formatarData', () => {
  it('troca AAAA-MM-DD por DD/MM/AAAA', () => {
    expect(formatarData('2026-10-05')).toBe('05/10/2026')
  })
})

describe('paraValorDaApi', () => {
  it.each([
    ['1.234,56', '1234.56'],
    ['12,5', '12.5'],
    ['12,50', '12.50'],
    ['12.50', '12.50'],
    [' 7 ', '7'],
    ['', ''],
  ])('%j → %j', (digitado, esperado) => {
    expect(paraValorDaApi(digitado)).toBe(esperado)
  })
})

describe('paraValorDigitado', () => {
  it('mostra o valor da API com vírgula, para editar', () => {
    expect(paraValorDigitado('1234.56')).toBe('1234,56')
  })
})

describe('emCentavos', () => {
  it.each([
    ['150.30', 15030n],
    ['0.05', 5n],
    ['1234.56', 123456n],
  ])('%s → %s', (valor, esperado) => {
    expect(emCentavos(valor)).toBe(esperado)
  })
})
