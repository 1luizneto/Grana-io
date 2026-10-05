// Mensagem geral acima do formulário: erros que não são de um campo e avisos (ex.: sessão expirada).
export default function AvisoFormulario({ mensagem, tipo = 'erro' }) {
  if (!mensagem) return null
  return (
    <p role="alert" className={`aviso aviso-${tipo}`}>
      {mensagem}
    </p>
  )
}
