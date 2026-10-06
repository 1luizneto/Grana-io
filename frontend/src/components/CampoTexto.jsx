import { useId } from 'react'

// Rótulo + campo + erros do campo, logo abaixo dele (FR-003, FR-014).
export default function CampoTexto({
  rotulo,
  nome,
  tipo = 'text',
  valor,
  aoMudar,
  erros = [],
  autoComplete,
}) {
  const id = useId()
  const idErros = `${id}-erros`
  const temErros = erros.length > 0

  return (
    <div className="campo">
      <label htmlFor={id}>{rotulo}</label>
      <input
        id={id}
        name={nome}
        type={tipo}
        value={valor}
        onChange={(evento) => aoMudar(evento.target.value)}
        autoComplete={autoComplete}
        aria-invalid={temErros || undefined}
        aria-describedby={temErros ? idErros : undefined}
      />
      {temErros && (
        <ul id={idErros} className="campo-erros">
          {erros.map((mensagem) => (
            <li key={mensagem}>{mensagem}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
