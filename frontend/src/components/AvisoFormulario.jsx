// Mensagem geral acima do formulário: erros que não são de um campo e avisos (ex.: sessão expirada).
// Sucesso usa role="status": é anunciado sem interromper (specs/009-tela-mes, R-07).
export default function AvisoFormulario({ mensagem, tipo = 'erro' }) {
  if (!mensagem) return null
  return (
    <p role={tipo === 'sucesso' ? 'status' : 'alert'} className={`aviso aviso-${tipo}`}>
      {mensagem}
    </p>
  )
}
