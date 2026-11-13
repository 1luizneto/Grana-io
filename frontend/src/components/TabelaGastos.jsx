import { formatarData, formatarMoeda } from '../utils/formatacao.js'

// Gastos do mês, na ordem da API (data e lançamento), formatados para exibição (FR-007).
export default function TabelaGastos({ mes, gastos, categorias, formas }) {
  const nomeCategoria = Object.fromEntries(categorias.map((item) => [item.id, item.nome]))
  const nomeForma = Object.fromEntries(formas.map((item) => [item.codigo, item.nome]))

  if (gastos.length === 0) return <p>Nenhum gasto neste mês.</p>

  return (
    <table className="tabela-gastos">
      <caption className="visualmente-oculto">Gastos de {mes.rotulo}</caption>
      <thead>
        <tr>
          <th scope="col">Data</th>
          <th scope="col">Descrição</th>
          <th scope="col">Categoria</th>
          <th scope="col">Pagamento</th>
          <th scope="col">Valor</th>
        </tr>
      </thead>
      <tbody>
        {gastos.map((gasto) => (
          <tr key={gasto.id}>
            <td data-rotulo="Data">{formatarData(gasto.data)}</td>
            <td data-rotulo="Descrição">{gasto.descricao}</td>
            <td data-rotulo="Categoria">{nomeCategoria[gasto.categoria] ?? '—'}</td>
            <td data-rotulo="Pagamento">{nomeForma[gasto.forma_pagamento] ?? '—'}</td>
            <td data-rotulo="Valor" className="valor">
              {formatarMoeda(gasto.valor)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
