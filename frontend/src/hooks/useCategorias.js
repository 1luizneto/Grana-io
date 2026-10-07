import { useCallback, useEffect, useState } from 'react'
import * as api from '../api/categorias.js'
import { interpretarErro } from '../api/erros.js'

// Categorias e paleta da pessoa conectada (docs/arquitetura.md §3: hook por recurso). Depois de
// cada alteração a lista é recarregada: a ordem e a cor automática vêm sempre da API.
export function useCategorias() {
  const [categorias, setCategorias] = useState([])
  const [cores, setCores] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erroCarregar, setErroCarregar] = useState(null)

  const carregar = useCallback(async () => {
    try {
      const [respostaCategorias, respostaCores] = await Promise.all([
        api.listarCategorias(),
        api.listarCores(),
      ])
      const falha = [respostaCategorias, respostaCores].find((resposta) => !resposta.ok)
      if (falha) {
        setErroCarregar((await interpretarErro(falha)).geral)
        return
      }
      setCategorias(await respostaCategorias.json())
      setCores(await respostaCores.json())
      setErroCarregar(null)
    } catch (falha) {
      // Sessão expirada é tratada pelo AuthProvider (vai ao login); o resto é falha de comunicação.
      setErroCarregar((await interpretarErro(falha)).geral)
    } finally {
      setCarregando(false)
    }
  }, [])

  useEffect(() => {
    carregar()
  }, [carregar])

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

  const criar = useCallback((dados) => executar(() => api.criarCategoria(dados)), [executar])
  const atualizar = useCallback(
    (id, dados) => executar(() => api.atualizarCategoria(id, dados)),
    [executar],
  )
  const excluir = useCallback((id) => executar(() => api.excluirCategoria(id)), [executar])

  return { categorias, cores, carregando, erroCarregar, criar, atualizar, excluir }
}
