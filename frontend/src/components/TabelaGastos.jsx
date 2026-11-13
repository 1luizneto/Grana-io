import { useState } from 'react'
import { emCentavos, formatarData, formatarMoeda } from '../utils/formatacao.js'
import CampoSelecao from './CampoSelecao.jsx'

const ORDENS = [
  { valor: 'data-antiga', rotulo: 'Data (mais antigo)' },
  { valor: 'data-recente', rotulo: 'Data (mais recente)' },
  { valor: 'maior-valor', rotulo: 'Maior valor' },
  { valor: 'menor-valor', rotulo: 'Menor valor' },
]

const comparar = (a, b) => (a < b ? -1 : a > b ? 1 : 0)

// Ordem de exibição (R-04): a lista chega da API por data e lançamento. Valores comparados em
// centavos inteiros (BigInt), sem ponto flutuante; o sort é estável, então empates mantêm a ordem
// da API.
function ordenar(gastos, ordem) {
  switch (ordem) {
    case 'data-recente':
      return [...gastos].reverse()
    case 'maior-valor':
      return [...gastos].sort((a, b) => comparar(emCentavos(b.valor), emCentavos(a.valor)))
    case 'menor-valor':
      return [...gastos].sort((a, b) => comparar(emCentavos(a.valor), emCentavos(b.valor)))
    default:
      return gastos
  }
}

// Gastos do mês com filtro por categoria e ordenação (FR-007). Sem aoEditar/aoExcluir (mês
// fechado), a coluna de ações não aparece.
export default function TabelaGastos({ mes, gastos, categorias, formas, aoEditar, aoExcluir }) {
  const [filtro, setFiltro] = useState('')
  const [ordem, setOrdem] = useState('data-antiga')
  const comAcoes = Boolean(aoEditar && aoExcluir)
  const nomeCategoria = Object.fromEntries(categorias.map((item) => [item.id, item.nome]))
  const nomeForma = Object.fromEntries(formas.map((item) => [item.codigo, item.nome]))

  if (gastos.length === 0) return <p>Nenhum gasto neste mês.</p>

  const visiveis = ordenar(
    filtro ? gastos.filter((gasto) => String(gasto.categoria) === filtro) : gastos,
    ordem,
  )

  return (
    <>
      <div className="controles-tabela">
        <CampoSelecao
          rotulo="Filtrar por categoria"
          nome="filtro"
          valor={filtro}
          aoMudar={setFiltro}
          opcoes={[
            { valor: '', rotulo: 'Todas as categorias' },
            ...categorias.map((item) => ({ valor: String(item.id), rotulo: item.nome })),
          ]}
        />
        <CampoSelecao
          rotulo="Ordenar por"
          nome="ordem"
          valor={ordem}
          aoMudar={setOrdem}
          opcoes={ORDENS}
        />
      </div>
      {visiveis.length === 0 ? (
        <p>Nenhum gasto nesta categoria.</p>
      ) : (
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
            {visiveis.map((gasto) => (
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
      )}
    </>
  )
}
