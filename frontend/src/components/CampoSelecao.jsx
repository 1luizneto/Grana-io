import { useId } from 'react'

// Rótulo + lista de opções + erros do campo, como o CampoTexto (specs/009-tela-mes).
// opcoes: [{ valor, rotulo }]; os valores circulam como texto, como no <select>.
export default function CampoSelecao({ rotulo, nome, valor, aoMudar, opcoes, erros = [] }) {
  const id = useId()
  const idErros = `${id}-erros`
  const temErros = erros.length > 0

  return (
    <div className="campo">
      <label htmlFor={id}>{rotulo}</label>
      <select
        id={id}
        name={nome}
        value={valor}
        onChange={(evento) => aoMudar(evento.target.value)}
        aria-invalid={temErros || undefined}
        aria-describedby={temErros ? idErros : undefined}
      >
        {opcoes.map((opcao) => (
          <option key={opcao.valor} value={opcao.valor}>
            {opcao.rotulo}
          </option>
        ))}
      </select>
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
