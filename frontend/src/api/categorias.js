import { requisitarAutenticada } from './client.js'

// Contrato: specs/006-categorias-gasto/contracts/api-categorias.md. Cada função devolve a Response;
// quem chama usa interpretarErro nas falhas.
const JSON_CABECALHO = { 'Content-Type': 'application/json' }

export function listarCategorias() {
  return requisitarAutenticada('/categorias/')
}

export function listarCores() {
  return requisitarAutenticada('/categorias/cores/')
}

export function criarCategoria(dados) {
  return requisitarAutenticada('/categorias/', {
    method: 'POST',
    headers: JSON_CABECALHO,
    body: JSON.stringify(dados),
  })
}

export function atualizarCategoria(id, dados) {
  return requisitarAutenticada(`/categorias/${id}/`, {
    method: 'PATCH',
    headers: JSON_CABECALHO,
    body: JSON.stringify(dados),
  })
}

// moverPara: categoria que recebe os gastos da excluída (specs/008-lancar-gastos, R-07).
export function excluirCategoria(id, moverPara) {
  const consulta = moverPara ? `?mover_para=${moverPara}` : ''
  return requisitarAutenticada(`/categorias/${id}/${consulta}`, { method: 'DELETE' })
}
