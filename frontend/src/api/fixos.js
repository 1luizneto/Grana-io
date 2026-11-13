import { requisitarAutenticada } from './client.js'

// Contrato: specs/010-gastos-fixos/contracts/api-fixos.md. Cada função devolve a Response.
const JSON_CABECALHO = { 'Content-Type': 'application/json' }

export function listarFixos() {
  return requisitarAutenticada('/fixos/')
}

export function criarFixo(dados) {
  return requisitarAutenticada('/fixos/', {
    method: 'POST',
    headers: JSON_CABECALHO,
    body: JSON.stringify(dados),
  })
}

export function atualizarFixo(id, dados) {
  return requisitarAutenticada(`/fixos/${id}/`, {
    method: 'PATCH',
    headers: JSON_CABECALHO,
    body: JSON.stringify(dados),
  })
}

export function excluirFixo(id) {
  return requisitarAutenticada(`/fixos/${id}/`, { method: 'DELETE' })
}
