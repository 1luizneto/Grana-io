import { useId } from 'react'

// Escolha de cor da paleta (FR-013; research R-09). As cores vêm da API; rádios nativos dão o
// uso por Tab e setas sem código extra. valor null = nenhuma escolhida (a API escolhe).
export default function SeletorCor({ cores, valor, aoMudar }) {
  const nome = useId()

  return (
    <fieldset className="seletor-cor">
      <legend>Cor</legend>
      {cores.map((cor) => (
        <label key={cor.codigo} className="opcao-cor">
          <input
            type="radio"
            name={nome}
            value={cor.codigo}
            checked={valor === cor.codigo}
            onChange={() => aoMudar(cor.codigo)}
          />
          <span className="amostra" style={{ background: cor.hex }} aria-hidden="true" />
          <span className="nome-cor">{cor.nome}</span>
        </label>
      ))}
    </fieldset>
  )
}
