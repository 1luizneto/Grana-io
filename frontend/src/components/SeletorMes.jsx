import { useState } from 'react'
import AvisoFormulario from './AvisoFormulario.jsx'
import CampoSelecao from './CampoSelecao.jsx'
import CampoTexto from './CampoTexto.jsx'

const SEM_ERROS = { campos: {}, geral: null }

export const NOMES_DOS_MESES = [
  'Janeiro',
  'Fevereiro',
  'Março',
  'Abril',
  'Maio',
  'Junho',
  'Julho',
  'Agosto',
  'Setembro',
  'Outubro',
  'Novembro',
  'Dezembro',
]

const OPCOES_MES = NOMES_DOS_MESES.map((nome, indice) => ({
  valor: String(indice + 1),
  rotulo: nome,
}))

// Sugestão do formulário: o mês seguinte ao mais recente; sem meses, o de hoje (R-06).
function sugerirNovoMes(meses) {
  const ultimo = meses.at(-1)
  if (!ultimo) {
    const hoje = new Date()
    return { mes: hoje.getMonth() + 1, ano: hoje.getFullYear() }
  }
  if (ultimo.mes === 12) return { mes: 1, ano: ultimo.ano + 1 }
  return { mes: ultimo.mes + 1, ano: ultimo.ano }
}

// Seletor do mês exibido e formulário "Novo mês" (specs/009-tela-mes/research.md, R-06).
export default function SeletorMes({ meses, selecionado, aoEscolher, criar }) {
  return (
    <div className="seletor-mes">
      {meses.length > 0 && (
        <div className="campo">
          <label htmlFor="escolher-mes">Escolher mês</label>
          <select
            id="escolher-mes"
            value={selecionado ?? ''}
            onChange={(evento) => aoEscolher(evento.target.value)}
          >
            {selecionado === undefined && <option value="">—</option>}
            {meses.map((mes) => (
              <option key={mes.id} value={String(mes.id)}>
                {mes.rotulo}
                {mes.fechado ? ' (fechado)' : ''}
              </option>
            ))}
          </select>
        </div>
      )}
      {/* key: a sugestão é recalculada quando a lista de meses muda. */}
      <FormularioNovoMes key={meses.length} meses={meses} criar={criar} />
    </div>
  )
}

function FormularioNovoMes({ meses, criar }) {
  const sugestao = sugerirNovoMes(meses)
  const [mes, setMes] = useState(String(sugestao.mes))
  const [ano, setAno] = useState(String(sugestao.ano))
  const [erro, setErro] = useState(SEM_ERROS)
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    if (enviando) return
    setEnviando(true)
    setErro(SEM_ERROS)
    const resultado = await criar({ mes: Number(mes), ano: ano === '' ? '' : Number(ano) })
    setEnviando(false)
    if (!resultado.ok) setErro(resultado.erro)
  }

  return (
    <form className="cartao formulario-novo-mes" aria-label="Novo mês" onSubmit={aoEnviar} noValidate>
      <AvisoFormulario mensagem={erro.geral} />
      <CampoSelecao
        rotulo="Mês"
        nome="mes"
        valor={mes}
        aoMudar={setMes}
        opcoes={OPCOES_MES}
        erros={erro.campos.mes}
      />
      <CampoTexto
        rotulo="Ano"
        nome="ano"
        tipo="number"
        valor={ano}
        aoMudar={setAno}
        erros={erro.campos.ano}
      />
      <button type="submit" disabled={enviando}>
        {enviando ? 'Criando…' : 'Criar mês'}
      </button>
    </form>
  )
}
