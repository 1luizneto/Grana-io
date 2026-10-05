// Sessão guardada no navegador (specs/005-telas-login-cadastro/data-model.md; research R-02).
// Fica no localStorage para sobreviver a fechar o navegador; nunca contém a senha.
export const CHAVE_SESSAO = 'grana.sessao'

function textoPreenchido(valor) {
  return typeof valor === 'string' && valor.trim() !== ''
}

function valida(sessao) {
  return (
    textoPreenchido(sessao?.acesso) &&
    textoPreenchido(sessao?.renovacao) &&
    textoPreenchido(sessao?.usuario?.nome)
  )
}

// Grava só os campos conhecidos: qualquer outro (ex.: senha) é descartado.
function normalizar({ acesso, renovacao, usuario }) {
  return { acesso, renovacao, usuario: { nome: usuario.nome, email: usuario.email } }
}

export function lerSessao() {
  const bruto = localStorage.getItem(CHAVE_SESSAO)
  if (bruto === null) return null
  try {
    const sessao = JSON.parse(bruto)
    if (valida(sessao)) return normalizar(sessao)
  } catch {
    // JSON inválido: tratado abaixo como sessão ausente.
  }
  apagarSessao()
  return null
}

export function salvarSessao(sessao) {
  localStorage.setItem(CHAVE_SESSAO, JSON.stringify(normalizar(sessao)))
}

export function apagarSessao() {
  localStorage.removeItem(CHAVE_SESSAO)
}
