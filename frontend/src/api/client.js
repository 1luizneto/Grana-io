// Cliente de API centralizado: os componentes nunca chamam fetch diretamente.
// Por padrão a API é chamada em /api, no mesmo endereço da interface (proxy do Vite);
// VITE_API_URL permite apontar para outra URL base, incluindo o /api (RNF-08).
const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

// Com o banco fora do ar, a API leva ~4 s para responder 503 (o DNS do Docker demora a
// desistir do host "db"); o limite precisa de folga acima disso.
const TIMEOUT_MS = 10000

export async function requisitar(caminho, opcoes = {}) {
  return fetch(`${API_BASE}${caminho}`, {
    headers: { Accept: 'application/json' },
    // Respostas da API são dinâmicas e não devem ir para o cache do navegador. Sem isso, o
    // Chromium enfileira GETs idênticos simultâneos (cache lock), o que estoura o timeout.
    cache: 'no-store',
    signal: AbortSignal.timeout(TIMEOUT_MS),
    ...opcoes,
  })
}
