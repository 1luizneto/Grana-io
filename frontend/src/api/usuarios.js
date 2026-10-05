import { requisitar } from './client.js'

// Contrato: specs/002-cadastro-usuario/contracts/api-cadastro.md.
export function cadastrar({ nome, email, senha, confirmacao_senha }) {
  return requisitar('/usuarios/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nome, email, senha, confirmacao_senha }),
  })
}
