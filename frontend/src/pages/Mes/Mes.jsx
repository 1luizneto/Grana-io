import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import AvisoFormulario from '../../components/AvisoFormulario.jsx'
import SeletorMes from '../../components/SeletorMes.jsx'
import { useMeses } from '../../hooks/useMeses.js'

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
  const { meses, carregando, erroCarregar, criar } = useMeses()
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
          {mes && <DetalheMes key={mes.id} mes={mes} />}
        </>
      )}
    </section>
  )
}

function DetalheMes({ mes }) {
  return (
    <div className="detalhe-mes">
      <header className="cabecalho-mes">
        <h2>{mes.rotulo}</h2>
        <span className="situacao-mes">{mes.fechado ? 'Fechado' : 'Aberto'}</span>
      </header>
    </div>
  )
}
