import { requisitar, requisitarAutenticada } from './client.js'

// Contrato: specs/003-login-logout/contracts/api-sessao.md. Cada função devolve a Response; quem
// chama usa interpretarErro nas falhas. A renovação fica dentro do client.js (renovação única).
const JSON_CABECALHO = { 'Content-Type': 'application/json' }

export function entrar(email, senha) {
  return requisitar('/auth/entrar/', {
    method: 'POST',
    headers: JSON_CABECALHO,
    body: JSON.stringify({ email, senha }),
  })
}

export function sair(renovacao) {
  return requisitarAutenticada('/auth/sair/', {
    method: 'POST',
    headers: JSON_CABECALHO,
    body: JSON.stringify({ renovacao }),
  })
}

export function obterEu() {
  return requisitarAutenticada('/usuarios/eu/')
}
