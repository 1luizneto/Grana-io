// Formatação pt-BR (specs/009-tela-mes/research.md, R-03). A interface não calcula valores
// financeiros (constituição, Princípio V; RNF-03): tudo aqui é manipulação de texto. Os valores
// chegam da API como texto com 2 casas e ponto decimal (ex.: "1234.50").

// "1234.50" → "R$ 1.234,50"
export function formatarMoeda(valor) {
  const texto = String(valor)
  const negativo = texto.startsWith('-')
  const [inteiro, centavos = '00'] = texto.replace('-', '').split('.')
  const comMilhar = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return `${negativo ? '-' : ''}R$ ${comMilhar},${centavos.padEnd(2, '0')}`
}

// "2026-10-05" → "05/10/2026"
export function formatarData(data) {
  const [ano, mes, dia] = data.split('-')
  return `${dia}/${mes}/${ano}`
}

// Valor digitado → valor para a API. Com vírgula, ela é o decimal e os pontos são milhar
// ("1.234,56" → "1234.56"); sem vírgula, fica como está ("12.50"). Quem valida é a API.
export function paraValorDaApi(digitado) {
  const texto = digitado.trim()
  return texto.includes(',') ? texto.replace(/\./g, '').replace(',', '.') : texto
}

// Valor da API → campo de edição ("1234.56" → "1234,56").
export function paraValorDigitado(valor) {
  return String(valor).replace('.', ',')
}

// "150.30" → 15030n, só para ordenar por valor sem ponto flutuante.
export function emCentavos(valor) {
  const [inteiro, centavos = ''] = String(valor).split('.')
  return BigInt(inteiro + centavos.padEnd(2, '0').slice(0, 2))
}
