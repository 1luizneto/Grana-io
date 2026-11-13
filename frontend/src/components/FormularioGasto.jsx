import { useRef, useState } from 'react'
import { paraValorDaApi, paraValorDigitado } from '../utils/formatacao.js'
import AvisoFormulario from './AvisoFormulario.jsx'
import CampoSelecao from './CampoSelecao.jsx'
import CampoTexto from './CampoTexto.jsx'

const SEM_ERROS = { campos: {}, geral: null }
const dois = (numero) => String(numero).padStart(2, '0')

// Data padrão (R-05): hoje, se estiver no mês exibido; senão o dia 1 do mês.
function dataPadrao(mes) {
  const hoje = new Date()
  if (hoje.getMonth() + 1 === mes.mes && hoje.getFullYear() === mes.ano) {
    return `${mes.ano}-${dois(mes.mes)}-${dois(hoje.getDate())}`
  }
  return `${mes.ano}-${dois(mes.mes)}-01`
}

function limitesDoMes(mes) {
  const ultimoDia = new Date(mes.ano, mes.mes, 0).getDate()
  return {
    min: `${mes.ano}-${dois(mes.mes)}-01`,
    max: `${mes.ano}-${dois(mes.mes)}-${dois(ultimoDia)}`,
  }
}

// Formulário rápido de gasto, para lançar e para editar (specs/009-tela-mes/research.md, R-05).
// Para trocar de modo, a página remonta o componente (key), e o estado começa do gasto em edição.
export default function FormularioGasto({
  mes,
  categorias,
  formas,
  gasto,
  salvar,
  aoCancelar,
  desabilitado = false,
}) {
  const editando = Boolean(gasto)
  const [descricao, setDescricao] = useState(gasto?.descricao ?? '')
  const [valor, setValor] = useState(gasto ? paraValorDigitado(gasto.valor) : '')
  const [data, setData] = useState(gasto?.data ?? dataPadrao(mes))
  const [categoria, setCategoria] = useState(gasto ? String(gasto.categoria) : '')
  const [forma, setForma] = useState(gasto?.forma_pagamento ?? '')
  const [erro, setErro] = useState(SEM_ERROS)
  const [enviando, setEnviando] = useState(false)
  const campoDescricao = useRef(null)
  const limites = limitesDoMes(mes)

  async function aoEnviar(evento) {
    evento.preventDefault()
    if (enviando) return
    setEnviando(true)
    setErro(SEM_ERROS)
    const resultado = await salvar({
      descricao,
      valor: paraValorDaApi(valor),
      data,
      mes: mes.id,
      categoria: categoria ? Number(categoria) : null,
      forma_pagamento: forma,
    })
    setEnviando(false)
    if (!resultado.ok) {
      setErro(resultado.erro)
      return
    }
    if (!editando) {
      // Pronto para o próximo: data e categoria ficam (lançar vários seguidos).
      setDescricao('')
      setValor('')
      setForma('')
      campoDescricao.current?.focus()
    }
  }

  const titulo = editando ? 'Editar gasto' : 'Lançar gasto'
  const rotuloBotao = editando
    ? enviando
      ? 'Salvando…'
      : 'Salvar alterações'
    : enviando
      ? 'Lançando…'
      : 'Lançar'
  // Erro de mês (ex.: inexistente) não tem campo na tela: vai para a mensagem geral.
  const geral = [erro.geral, ...(erro.campos.mes ?? [])].filter(Boolean).join(' ')

  return (
    <form className="cartao formulario-gasto" aria-label={titulo} onSubmit={aoEnviar} noValidate>
      <h2>{titulo}</h2>
      <AvisoFormulario mensagem={geral} />
      <fieldset disabled={desabilitado}>
        <CampoTexto
          ref={campoDescricao}
          rotulo="Descrição"
          nome="descricao"
          valor={descricao}
          aoMudar={setDescricao}
          erros={erro.campos.descricao}
        />
        <CampoTexto
          rotulo="Valor"
          nome="valor"
          valor={valor}
          aoMudar={setValor}
          erros={erro.campos.valor}
          inputMode="decimal"
          placeholder="0,00"
        />
        <CampoTexto
          rotulo="Data"
          nome="data"
          tipo="date"
          valor={data}
          aoMudar={setData}
          erros={erro.campos.data}
          min={limites.min}
          max={limites.max}
        />
        <CampoSelecao
          rotulo="Categoria"
          nome="categoria"
          valor={categoria}
          aoMudar={setCategoria}
          opcoes={[
            { valor: '', rotulo: 'Escolha uma categoria' },
            ...categorias.map((item) => ({ valor: String(item.id), rotulo: item.nome })),
          ]}
          erros={erro.campos.categoria}
        />
        <CampoSelecao
          rotulo="Forma de pagamento"
          nome="forma_pagamento"
          valor={forma}
          aoMudar={setForma}
          opcoes={[
            { valor: '', rotulo: 'Não informar' },
            ...formas.map((item) => ({ valor: item.codigo, rotulo: item.nome })),
          ]}
          erros={erro.campos.forma_pagamento}
        />
        <div className="acoes">
          <button type="submit" disabled={enviando}>
            {rotuloBotao}
          </button>
          {editando && (
            <button type="button" className="secundario" onClick={aoCancelar}>
              Cancelar edição
            </button>
          )}
        </div>
      </fieldset>
    </form>
  )
}
