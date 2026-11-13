import { useState } from 'react'
import AvisoFormulario from '../../components/AvisoFormulario.jsx'
import CampoSelecao from '../../components/CampoSelecao.jsx'
import CampoTexto from '../../components/CampoTexto.jsx'
import SeletorCor from '../../components/SeletorCor.jsx'
import { useCategorias } from '../../hooks/useCategorias.js'

const SEM_ERROS = { campos: {}, geral: null }

// Tela de categorias (US5; specs/006-categorias-gasto/contracts/tela-categorias.md).
export default function Categorias() {
  const { categorias, cores, carregando, erroCarregar, criar, atualizar, excluir } = useCategorias()
  const porCodigo = Object.fromEntries(cores.map((cor) => [cor.codigo, cor]))

  return (
    <section className="categorias">
      <h1>Categorias</h1>
      <FormularioNova cores={cores} criar={criar} />
      <AvisoFormulario mensagem={erroCarregar} />
      {carregando ? (
        <p>Carregando categorias…</p>
      ) : categorias.length === 0 ? (
        !erroCarregar && <p>Nenhuma categoria. Crie a primeira acima.</p>
      ) : (
        <ul className="lista-categorias">
          {categorias.map((categoria) => (
            <LinhaCategoria
              key={categoria.id}
              categoria={categoria}
              cor={porCodigo[categoria.cor]}
              cores={cores}
              outras={categorias.filter((outra) => outra.id !== categoria.id)}
              atualizar={atualizar}
              excluir={excluir}
            />
          ))}
        </ul>
      )}
    </section>
  )
}

function FormularioNova({ cores, criar }) {
  const [nome, setNome] = useState('')
  const [cor, setCor] = useState(null)
  const [erro, setErro] = useState(SEM_ERROS)
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    if (enviando) return
    setEnviando(true)
    setErro(SEM_ERROS)
    // Sem cor escolhida, a API atribui a primeira cor livre (FR-007).
    const resultado = await criar(cor ? { nome, cor } : { nome })
    if (resultado.ok) {
      setNome('')
      setCor(null)
    } else {
      setErro(resultado.erro)
    }
    setEnviando(false)
  }

  return (
    <form className="cartao formulario-categoria" aria-label="Nova categoria" onSubmit={aoEnviar} noValidate>
      <AvisoFormulario mensagem={erro.geral} />
      <CampoTexto rotulo="Nome" nome="nome" valor={nome} aoMudar={setNome} erros={erro.campos.nome} />
      <SeletorCor cores={cores} valor={cor} aoMudar={setCor} />
      {erro.campos.cor && <AvisoFormulario mensagem={erro.campos.cor.join(' ')} />}
      <button type="submit" disabled={enviando}>
        {enviando ? 'Adicionando…' : 'Adicionar'}
      </button>
    </form>
  )
}

function LinhaCategoria({ categoria, cor, cores, outras, atualizar, excluir }) {
  const [editando, setEditando] = useState(false)
  const [excluindo, setExcluindo] = useState(false)
  const [nome, setNome] = useState(categoria.nome)
  const [codigoCor, setCodigoCor] = useState(categoria.cor)
  const [erro, setErro] = useState(SEM_ERROS)
  const [enviando, setEnviando] = useState(false)

  function abrirEdicao() {
    setNome(categoria.nome)
    setCodigoCor(categoria.cor)
    setErro(SEM_ERROS)
    setEditando(true)
  }

  async function aoSalvar(evento) {
    evento.preventDefault()
    if (enviando) return
    setEnviando(true)
    const resultado = await atualizar(categoria.id, { nome, cor: codigoCor })
    setEnviando(false)
    if (resultado.ok) setEditando(false)
    else setErro(resultado.erro)
  }

  if (excluindo) {
    return (
      <li className="linha-categoria editando">
        <ConfirmarExclusao
          categoria={categoria}
          outras={outras}
          excluir={excluir}
          aoCancelar={() => setExcluindo(false)}
        />
      </li>
    )
  }

  if (editando) {
    return (
      <li className="linha-categoria editando">
        <form aria-label={`Editar ${categoria.nome}`} onSubmit={aoSalvar} noValidate>
          <AvisoFormulario mensagem={erro.geral} />
          <CampoTexto rotulo="Nome" nome="nome" valor={nome} aoMudar={setNome} erros={erro.campos.nome} />
          <SeletorCor cores={cores} valor={codigoCor} aoMudar={setCodigoCor} />
          {erro.campos.cor && <AvisoFormulario mensagem={erro.campos.cor.join(' ')} />}
          <div className="acoes">
            <button type="submit" disabled={enviando}>
              {enviando ? 'Salvando…' : 'Salvar'}
            </button>
            <button type="button" className="secundario" onClick={() => setEditando(false)}>
              Cancelar
            </button>
          </div>
        </form>
      </li>
    )
  }

  return (
    <li className="linha-categoria">
      <span className="amostra" style={{ background: cor?.hex }} aria-hidden="true" />
      <span className="nome-categoria">{categoria.nome}</span>
      <span className="visualmente-oculto">Cor: {cor?.nome}</span>
      <div className="acoes">
        <button type="button" className="secundario" aria-label={`Editar ${categoria.nome}`} onClick={abrirEdicao}>
          Editar
        </button>
        <button
          type="button"
          className="secundario"
          aria-label={`Excluir ${categoria.nome}`}
          onClick={() => setExcluindo(true)}
        >
          Excluir
        </button>
      </div>
    </li>
  )
}

// Confirmação da exclusão com o destino dos gastos (spec 009, research R-09). A tela não sabe se a
// categoria tem gastos: o destino vai sempre, e a API o ignora quando não há gastos.
function ConfirmarExclusao({ categoria, outras, excluir, aoCancelar }) {
  const sugerida = outras.find((outra) => outra.nome === 'Outros') ?? outras[0]
  const [destino, setDestino] = useState(sugerida ? String(sugerida.id) : '')
  const [erro, setErro] = useState(null)
  const [enviando, setEnviando] = useState(false)

  async function aoConfirmar(evento) {
    evento.preventDefault()
    if (enviando) return
    setEnviando(true)
    const resultado = await excluir(categoria.id, destino || undefined)
    // No sucesso a linha some com a lista recarregada.
    if (!resultado.ok) {
      setEnviando(false)
      setErro(
        [resultado.erro.geral, ...(resultado.erro.campos.mover_para ?? [])]
          .filter(Boolean)
          .join(' '),
      )
    }
  }

  return (
    <form aria-label={`Excluir ${categoria.nome}`} onSubmit={aoConfirmar} noValidate>
      <p>Excluir a categoria "{categoria.nome}"?</p>
      <AvisoFormulario mensagem={erro} />
      {outras.length > 0 ? (
        <CampoSelecao
          rotulo="Mover os gastos para"
          nome="mover_para"
          valor={destino}
          aoMudar={setDestino}
          opcoes={outras.map((outra) => ({ valor: String(outra.id), rotulo: outra.nome }))}
        />
      ) : (
        <p>Não há outra categoria para receber gastos.</p>
      )}
      <div className="acoes">
        <button type="submit" className="perigo" disabled={enviando}>
          {enviando ? 'Excluindo…' : 'Excluir'}
        </button>
        <button type="button" className="secundario" onClick={aoCancelar}>
          Cancelar
        </button>
      </div>
    </form>
  )
}
