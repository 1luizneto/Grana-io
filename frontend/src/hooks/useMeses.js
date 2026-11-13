import { useCallback, useEffect, useState } from 'react'
import { interpretarErro } from '../api/erros.js'
import * as api from '../api/meses.js'

// Meses de referência da pessoa conectada (specs/009-tela-mes/research.md, R-02). Depois de cada
// alteração a lista é recarregada: ordem e situação vêm sempre da API.
export function useMeses() {
  const [meses, setMeses] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erroCarregar, setErroCarregar] = useState(null)

  const carregar = useCallback(async () => {
    try {
      const resposta = await api.listarMeses()
      if (!resposta.ok) {
        setErroCarregar((await interpretarErro(resposta)).geral)
        return
      }
      setMeses(await resposta.json())
      setErroCarregar(null)
    } catch (falha) {
      setErroCarregar((await interpretarErro(falha)).geral)
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregar()
  }, [carregar])

  // Devolve { ok: true, dados } (corpo da resposta, quando houver) ou { ok: false, erro }.
  const executar = useCallback(
    async (operacao) => {
      try {
        const resposta = await operacao()
        if (!resposta.ok) return { ok: false, erro: await interpretarErro(resposta) }
        const dados = resposta.status === 204 ? null : await resposta.json()
        await carregar()
        return { ok: true, dados }
      } catch (falha) {
        return { ok: false, erro: await interpretarErro(falha) }
      }
    },
    [carregar],
  )

  const criar = useCallback((dados) => executar(() => api.criarMes(dados)), [executar])
  const definirFechado = useCallback(
    (id, fechado) => executar(() => api.atualizarMes(id, { fechado })),
    [executar],
  )
  const excluir = useCallback((id) => executar(() => api.excluirMes(id)), [executar])

  return { meses, carregando, erroCarregar, criar, definirFechado, excluir }
}
