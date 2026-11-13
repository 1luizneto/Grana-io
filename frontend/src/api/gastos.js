import { requisitarAutenticada } from './client.js'

// Contrato: specs/008-lancar-gastos/contracts/api-gastos.md. Cada função devolve a Response.
const JSON_CABECALHO = { 'Content-Type': 'application/json' }

export function listarGastos(mesId) {
  return requisitarAutenticada(`/gastos/?mes=${mesId}`)
}

export function listarFormasPagamento() {
  return requisitarAutenticada('/gastos/formas-pagamento/')
}

export function criarGasto(dados) {
  return requisitarAutenticada('/gastos/', {
    method: 'POST',
    headers: JSON_CABECALHO,
    body: JSON.stringify(dados),
  })
}

export function atualizarGasto(id, dados) {
  return requisitarAutenticada(`/gastos/${id}/`, {
    method: 'PATCH',
    headers: JSON_CABECALHO,
    body: JSON.stringify(dados),
  })
}

export function excluirGasto(id) {
  return requisitarAutenticada(`/gastos/${id}/`, { method: 'DELETE' })
}
