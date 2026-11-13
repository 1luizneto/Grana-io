import { useCallback, useEffect, useState } from 'react'
import { interpretarErro } from '../api/erros.js'
import * as api from '../api/fixos.js'
import { listarFormasPagamento } from '../api/gastos.js'

// Gastos fixos da pessoa conectada (specs/010-gastos-fixos). Depois de cada alteração a lista é
// recarregada: a ordem (dia de vencimento) vem da API.
export function useFixos() {
  const [fixos, setFixos] = useState([])
  const [formas, setFormas] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erroCarregar, setErroCarregar] = useState(null)

  const carregar = useCallback(async () => {
    try {
      const resposta = await api.listarFixos()
      if (!resposta.ok) {
        setErroCarregar((await interpretarErro(resposta)).geral)
        return
      }
      setFixos(await resposta.json())
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

  useEffect(() => {
    let ativo = true
    listarFormasPagamento()
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

  const criar = useCallback((dados) => executar(() => api.criarFixo(dados)), [executar])
  const atualizar = useCallback(
    (id, dados) => executar(() => api.atualizarFixo(id, dados)),
    [executar],
  )
  const excluir = useCallback((id) => executar(() => api.excluirFixo(id)), [executar])

  return { fixos, formas, carregando, erroCarregar, criar, atualizar, excluir }
}
