import { requisitarAutenticada } from './client.js'

// Contratos: specs/007-mes-referencia/contracts/api-meses.md e, para os totais,
// specs/008-lancar-gastos/contracts/api-gastos.md. Cada função devolve a Response.
const JSON_CABECALHO = { 'Content-Type': 'application/json' }

export function listarMeses() {
  return requisitarAutenticada('/meses/')
}

export function criarMes(dados) {
  return requisitarAutenticada('/meses/', {
    method: 'POST',
    headers: JSON_CABECALHO,
    body: JSON.stringify(dados),
  })
}

export function atualizarMes(id, dados) {
  return requisitarAutenticada(`/meses/${id}/`, {
    method: 'PATCH',
    headers: JSON_CABECALHO,
    body: JSON.stringify(dados),
  })
}

export function excluirMes(id) {
  return requisitarAutenticada(`/meses/${id}/`, { method: 'DELETE' })
}

export function buscarTotais(id) {
  return requisitarAutenticada(`/meses/${id}/totais/`)
}
