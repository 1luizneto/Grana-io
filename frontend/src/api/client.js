import { apagarSessao, lerSessao, salvarSessao } from '../auth/armazenamento.js'

// Cliente de API centralizado: os componentes nunca chamam fetch diretamente.
// Por padrão a API é chamada em /api, no mesmo endereço da interface (proxy do Vite);
// VITE_API_URL permite apontar para outra URL base, incluindo o /api (RNF-08).
const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

// Com o banco fora do ar, a API leva ~4 s para responder 503 (o DNS do Docker demora a
// desistir do host "db"); o limite precisa de folga acima disso.
const TIMEOUT_MS = 10000

export async function requisitar(caminho, opcoes = {}) {
  const { headers, ...resto } = opcoes
  return fetch(`${API_BASE}${caminho}`, {
    // Respostas da API são dinâmicas e não devem ir para o cache do navegador. Sem isso, o
    // Chromium enfileira GETs idênticos simultâneos (cache lock), o que estoura o timeout.
    cache: 'no-store',
    signal: AbortSignal.timeout(TIMEOUT_MS),
    ...resto,
    headers: { Accept: 'application/json', ...headers },
  })
}

// --- Requisições autenticadas (specs/005-telas-login-cadastro, research R-03) ---

export class SessaoExpirada extends Error {
  constructor() {
    super('Sessão expirada ou encerrada.')
    this.name = 'SessaoExpirada'
  }
}

let aoExpirar = null
// Promessa da renovação em andamento: cada credencial de renovação vale uma única vez (spec 003),
// então duas renovações em paralelo derrubariam a sessão. Todas as requisições esperam a mesma.
let renovacaoEmAndamento = null

// O AuthProvider registra aqui o que fazer quando a sessão não pode mais ser renovada.
export function registrarAoExpirar(funcao) {
  aoExpirar = funcao
  return () => {
    if (aoExpirar === funcao) aoExpirar = null
  }
}

export function _reiniciarParaTestes() {
  aoExpirar = null
  renovacaoEmAndamento = null
}

function expirar() {
  apagarSessao()
  aoExpirar?.()
  return new SessaoExpirada()
}

function comCredencial(opcoes, acesso) {
  return { ...opcoes, headers: { ...opcoes.headers, Authorization: `Bearer ${acesso}` } }
}

async function codigoDoErro(resposta) {
  try {
    return (await resposta.clone().json())?.code ?? null
  } catch {
    return null
  }
}

async function renovar(renovacaoUsada) {
  const resposta = await requisitar('/auth/renovar/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ renovacao: renovacaoUsada }),
  })
  const atual = lerSessao()
  if (resposta.ok) {
    if (!atual) throw expirar() // a pessoa saiu (em outra aba) enquanto renovava
    const par = await resposta.json()
    salvarSessao({ ...atual, acesso: par.acesso, renovacao: par.renovacao })
    return par.acesso
  }
  if (resposta.status === 400 || resposta.status === 401) {
    // Outra aba renovou primeiro e gravou o par novo: usa o dela em vez de expirar.
    if (atual && atual.renovacao !== renovacaoUsada) return atual.acesso
    throw expirar()
  }
  throw new Error(`Falha ao renovar a sessão (HTTP ${resposta.status}).`)
}

function renovarUmaVez(renovacaoUsada) {
  renovacaoEmAndamento ??= renovar(renovacaoUsada).finally(() => {
    renovacaoEmAndamento = null
  })
  return renovacaoEmAndamento
}

// Envia a credencial de acesso; se ela venceu, renova (uma vez por vez) e repete a requisição.
// Lança SessaoExpirada quando não há sessão ou ela não pode mais ser renovada.
export async function requisitarAutenticada(caminho, opcoes = {}) {
  const sessao = lerSessao()
  if (!sessao) throw expirar()

  const resposta = await requisitar(caminho, comCredencial(opcoes, sessao.acesso))
  if (resposta.status !== 401) return resposta

  // Só a credencial vencida ou inválida é renovável; sem credencial ou conta desativada, não.
  if ((await codigoDoErro(resposta)) !== 'token_not_valid') throw expirar()

  // Se outra requisição já renovou depois que esta saiu, basta usar o acesso novo.
  const atual = lerSessao()
  const acesso =
    atual && atual.acesso !== sessao.acesso ? atual.acesso : await renovarUmaVez(sessao.renovacao)
  return requisitar(caminho, comCredencial(opcoes, acesso))
}
