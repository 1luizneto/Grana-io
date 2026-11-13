import { useCallback, useEffect, useState } from 'react'
import { interpretarErro } from '../api/erros.js'
import * as api from '../api/gastos.js'
import { buscarTotais } from '../api/meses.js'

// Gastos e totais de um mês (specs/009-tela-mes/research.md, R-02). Os totais vêm prontos da API
// (RNF-03): depois de cada alteração, gastos e totais são recarregados juntos.
export function useGastosDoMes(mesId) {
  const [gastos, setGastos] = useState([])
  const [totais, setTotais] = useState(null)
  const [formas, setFormas] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erroCarregar, setErroCarregar] = useState(null)

  const carregar = useCallback(async () => {
    if (!mesId) return
    try {
      const respostas = await Promise.all([api.listarGastos(mesId), buscarTotais(mesId)])
      const falha = respostas.find((resposta) => !resposta.ok)
      if (falha) {
        setErroCarregar((await interpretarErro(falha)).geral)
        return
      }
      const [listaGastos, totaisDoMes] = await Promise.all(respostas.map((r) => r.json()))
      setGastos(listaGastos)
      setTotais(totaisDoMes)
      setErroCarregar(null)
    } catch (falha) {
      setErroCarregar((await interpretarErro(falha)).geral)
    } finally {
      setCarregando(false)
    }
  }, [mesId])

  useEffect(() => {
    setCarregando(true)
    carregar()
  }, [carregar])

  // As formas de pagamento não mudam: carregadas uma vez.
  useEffect(() => {
    let ativo = true
    api
      .listarFormasPagamento()
      .then((resposta) => (resposta.ok ? resposta.json() : []))
      .then((lista) => ativo && setFormas(lista))
      .catch(() => {})
    return () => {
      ativo = false
    }
  }, [])

  const executar = useCallback(
    async (operacao) => {
      try {
        const resposta = await operacao()
        if (!resposta.ok) return { ok: false, erro: await interpretarErro(resposta) }
        await carregar()
        return { ok: true }
      } catch (falha) {
        return { ok: false, erro: await interpretarErro(falha) }
      }
    },
    [carregar],
  )

  const criar = useCallback((dados) => executar(() => api.criarGasto(dados)), [executar])
  const atualizar = useCallback(
    (id, dados) => executar(() => api.atualizarGasto(id, dados)),
    [executar],
  )
  const excluir = useCallback((id) => executar(() => api.excluirGasto(id)), [executar])

  return { gastos, totais, formas, carregando, erroCarregar, criar, atualizar, excluir }
}
