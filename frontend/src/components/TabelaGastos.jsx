import { formatarData, formatarMoeda } from '../utils/formatacao.js'

// Gastos do mês, na ordem da API (data e lançamento), formatados para exibição (FR-007).
// Sem aoEditar/aoExcluir (mês fechado), a coluna de ações não aparece.
export default function TabelaGastos({ mes, gastos, categorias, formas, aoEditar, aoExcluir }) {
  const comAcoes = Boolean(aoEditar && aoExcluir)
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
          {comAcoes && (
            <th scope="col">
              <span className="visualmente-oculto">Ações</span>
            </th>
          )}
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
            {comAcoes && (
              <td className="acoes">
                <button
                  type="button"
                  className="secundario"
                  aria-label={`Editar ${gasto.descricao}`}
                  onClick={() => aoEditar(gasto)}
                >
                  Editar
                </button>
                <button
                  type="button"
                  className="secundario"
                  aria-label={`Excluir ${gasto.descricao}`}
                  onClick={() => aoExcluir(gasto)}
                >
                  Excluir
                </button>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
