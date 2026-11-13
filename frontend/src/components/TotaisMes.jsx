import { useId } from 'react'
import { formatarMoeda } from '../utils/formatacao.js'

// Totais do mês como a API calculou (FR-008; RNF-03): a tela não soma nada.
export default function TotaisMes({ totais, cores }) {
  const idTitulo = useId()
  const hexPorCodigo = Object.fromEntries(cores.map((cor) => [cor.codigo, cor.hex]))

  return (
    <section className="cartao totais-mes" aria-labelledby={idTitulo}>
      <h2 id={idTitulo}>Totais</h2>
      <p className="total-mes">
        <span>Total do mês</span>
        <strong>{formatarMoeda(totais.total)}</strong>
      </p>
      {totais.por_categoria.length > 0 && (
        <ul className="totais-categorias">
          {totais.por_categoria.map((item) => (
            <li key={item.categoria}>
              <span
                className="amostra"
                style={{ background: hexPorCodigo[item.cor] }}
                aria-hidden="true"
              />
              <span className="nome-categoria">{item.nome}</span>
              <span className="quantidade">
                {item.quantidade === 1 ? '1 gasto' : `${item.quantidade} gastos`}
              </span>
              <strong>{formatarMoeda(item.total)}</strong>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
