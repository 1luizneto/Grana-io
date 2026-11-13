import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import AvisoFormulario from '../../components/AvisoFormulario.jsx'
import FormularioGasto from '../../components/FormularioGasto.jsx'
import SeletorMes from '../../components/SeletorMes.jsx'
import TabelaGastos from '../../components/TabelaGastos.jsx'
import TotaisMes from '../../components/TotaisMes.jsx'
import { useCategorias } from '../../hooks/useCategorias.js'
import { useGastosDoMes } from '../../hooks/useGastosDoMes.js'
import { useMeses } from '../../hooks/useMeses.js'
import { formatarMoeda } from '../../utils/formatacao.js'

// Mês inicial (FR-003): o de hoje, se existir; senão o mais recente da lista (ordem da API).
function escolherMesInicial(meses) {
  const hoje = new Date()
  const atual = meses.find((m) => m.mes === hoje.getMonth() + 1 && m.ano === hoje.getFullYear())
  return atual ?? meses.at(-1)
}

// Tela "Gastos do mês" (US-27; specs/009-tela-mes/contracts/tela-mes.md).
export default function Mes() {
  const { id } = useParams()
  const navegar = useNavigate()
  const { meses, carregando, erroCarregar, criar, definirFechado, excluir } = useMeses()
  const [aviso, setAviso] = useState(null)
  const mes = meses.find((item) => String(item.id) === id)

  // /meses sem id: vai para o mês inicial (replace: voltar não cai de novo aqui).
  useEffect(() => {
    if (carregando || id || meses.length === 0) return
    navegar(`/meses/${escolherMesInicial(meses).id}`, { replace: true })
  }, [carregando, id, meses, navegar])

  function avisar(tipo, mensagem) {
    setAviso({ tipo, mensagem })
  }

  async function aoCriarMes(dados) {
    const resultado = await criar(dados)
    if (resultado.ok) {
      avisar('sucesso', 'Mês criado.')
      navegar(`/meses/${resultado.dados.id}`)
    }
    return resultado
  }

  async function aoDefinirFechado(alvo, fechado) {
    const resultado = await definirFechado(alvo.id, fechado)
    if (resultado.ok) avisar('sucesso', fechado ? 'Mês fechado.' : 'Mês reaberto.')
    else avisar('erro', resultado.erro.geral)
  }

  async function aoExcluirMes(alvo) {
    if (!window.confirm(`Excluir o mês ${alvo.rotulo}?`)) return
    const resultado = await excluir(alvo.id)
    if (resultado.ok) {
      avisar('sucesso', 'Mês excluído.')
      navegar('/meses', { replace: true })
    } else {
      avisar('erro', resultado.erro.geral)
    }
  }

  function aoEscolher(novoId) {
    setAviso(null)
    navegar(`/meses/${novoId}`)
  }

  return (
    <section className="pagina-mes">
      <h1>Gastos do mês</h1>
      <AvisoFormulario mensagem={erroCarregar} />
      <AvisoFormulario mensagem={aviso?.mensagem} tipo={aviso?.tipo} />
      {carregando ? (
        <p>Carregando meses…</p>
      ) : (
        <>
          {meses.length === 0 && !erroCarregar && <p>Nenhum mês criado. Crie o primeiro abaixo.</p>}
          <SeletorMes
            meses={meses}
            selecionado={mes ? String(mes.id) : undefined}
            aoEscolher={aoEscolher}
            criar={aoCriarMes}
          />
          {id && !mes && <p>Mês não encontrado.</p>}
          {mes && (
            <DetalheMes
              key={mes.id}
              mes={mes}
              avisar={avisar}
              aoDefinirFechado={aoDefinirFechado}
              aoExcluirMes={aoExcluirMes}
            />
          )}
        </>
      )}
    </section>
  )
}

// Um mês: cabeçalho, totais, formulário e tabela. Remontado ao trocar de mês (key).
function DetalheMes({ mes, avisar, aoDefinirFechado, aoExcluirMes }) {
  const { gastos, totais, formas, carregando, erroCarregar, criar, atualizar, excluir } =
    useGastosDoMes(mes.id)
  const { categorias, cores } = useCategorias()
  const [emEdicao, setEmEdicao] = useState(null)

  // Mês fechado durante uma edição: a edição é abandonada (a API recusaria).
  if (mes.fechado && emEdicao) setEmEdicao(null)

  async function aoSalvar(dados) {
    const resultado = emEdicao ? await atualizar(emEdicao.id, dados) : await criar(dados)
    if (resultado.ok) {
      avisar('sucesso', emEdicao ? 'Gasto atualizado.' : 'Gasto lançado.')
      setEmEdicao(null)
    }
    return resultado
  }

  async function aoExcluir(gasto) {
    if (!window.confirm(`Excluir o gasto "${gasto.descricao}" de ${formatarMoeda(gasto.valor)}?`)) {
      return
    }
    const resultado = await excluir(gasto.id)
    if (resultado.ok) {
      avisar('sucesso', 'Gasto excluído.')
      if (emEdicao?.id === gasto.id) setEmEdicao(null)
    } else {
      avisar('erro', resultado.erro.geral)
    }
  }

  return (
    <div className="detalhe-mes">
      <header className="cabecalho-mes">
        <h2>{mes.rotulo}</h2>
        <span className={`situacao-mes ${mes.fechado ? 'fechado' : 'aberto'}`}>
          {mes.fechado ? 'Fechado' : 'Aberto'}
        </span>
        <div className="acoes">
          <button
            type="button"
            className="secundario"
            onClick={() => aoDefinirFechado(mes, !mes.fechado)}
          >
            {mes.fechado ? 'Reabrir mês' : 'Fechar mês'}
          </button>
          <button type="button" className="secundario" onClick={() => aoExcluirMes(mes)}>
            Excluir mês
          </button>
        </div>
      </header>
      {mes.fechado && (
        <p className="aviso aviso-info">Mês fechado. Reabra o mês para lançar ou alterar gastos.</p>
      )}
      <AvisoFormulario mensagem={erroCarregar} />
      {carregando ? (
        <p>Carregando gastos…</p>
      ) : (
        <>
          {totais && <TotaisMes totais={totais} cores={cores} />}
          <FormularioGasto
            key={emEdicao?.id ?? 'novo'}
            mes={mes}
            categorias={categorias}
            formas={formas}
            gasto={emEdicao}
            salvar={aoSalvar}
            aoCancelar={() => setEmEdicao(null)}
            desabilitado={mes.fechado}
          />
          <section className="gastos-mes" aria-labelledby={`gastos-${mes.id}`}>
            <h2 id={`gastos-${mes.id}`}>Gastos</h2>
            <TabelaGastos
              mes={mes}
              gastos={gastos}
              categorias={categorias}
              formas={formas}
              aoEditar={mes.fechado ? undefined : setEmEdicao}
              aoExcluir={mes.fechado ? undefined : aoExcluir}
            />
          </section>
        </>
      )}
    </div>
  )
}
