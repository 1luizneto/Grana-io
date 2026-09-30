import { requisitar } from './client.js'

// Contrato: specs/001-infra-docker/contracts/api-health.md ("Consumo pelo frontend").
// Retorna 'ok' | 'banco-indisponivel' | 'inacessivel' e nunca lança exceção.
export async function obterSaude() {
  try {
    const resposta = await requisitar('/health/')
    if (resposta.status === 503) return 'banco-indisponivel'
    if (!resposta.ok) return 'inacessivel'
    const corpo = await resposta.json()
    return corpo.database === 'ok' ? 'ok' : 'inacessivel'
  } catch {
    return 'inacessivel'
  }
}
