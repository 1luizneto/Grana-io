// Traduz respostas de erro da API para o que as telas exibem (research R-06). As mensagens vêm da
// API como estão (constituição, Princípio V): a interface só decide onde mostrá-las.
export const MENSAGEM_FALHA_COMUNICACAO = 'Não foi possível falar com o servidor. Tente novamente.'

const FALHA = { campos: {}, geral: MENSAGEM_FALHA_COMUNICACAO }
const GERAIS = ['non_field_errors', 'detail']

function ehResposta(alvo) {
  return typeof alvo?.status === 'number' && typeof alvo?.json === 'function'
}

function comoLista(valor) {
  return Array.isArray(valor) ? valor.map(String) : [String(valor)]
}

// Devolve { campos: { nomeDoCampo: [mensagens] }, geral: mensagem | null }.
export async function interpretarErro(alvo) {
  if (!ehResposta(alvo)) return FALHA

  let corpo
  try {
    corpo = await alvo.json()
  } catch {
    return FALHA
  }
  if (!corpo || typeof corpo !== 'object') return FALHA

  if (alvo.status === 400) {
    const campos = {}
    const gerais = []
    for (const [campo, mensagens] of Object.entries(corpo)) {
      if (GERAIS.includes(campo)) gerais.push(...comoLista(mensagens))
      else campos[campo] = comoLista(mensagens)
    }
    return { campos, geral: gerais.length ? gerais.join(' ') : null }
  }

  if ([401, 403, 429].includes(alvo.status) && typeof corpo.detail === 'string') {
    return { campos: {}, geral: corpo.detail }
  }

  return FALHA
}
