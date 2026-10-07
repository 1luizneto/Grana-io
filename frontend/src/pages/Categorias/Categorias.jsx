import { useState } from 'react'
import AvisoFormulario from '../../components/AvisoFormulario.jsx'
import CampoTexto from '../../components/CampoTexto.jsx'
import SeletorCor from '../../components/SeletorCor.jsx'
import { useCategorias } from '../../hooks/useCategorias.js'

const SEM_ERROS = { campos: {}, geral: null }

// Tela de categorias (US5; specs/006-categorias-gasto/contracts/tela-categorias.md).
export default function Categorias() {
  const { categorias, cores, carregando, erroCarregar, criar, atualizar, excluir } = useCategorias()
  const [erroExcluir, setErroExcluir] = useState(null)
  const porCodigo = Object.fromEntries(cores.map((cor) => [cor.codigo, cor]))

  async function aoExcluir(categoria) {
    if (!window.confirm(`Excluir a categoria "${categoria.nome}"?`)) return
    const resultado = await excluir(categoria.id)
    setErroExcluir(resultado.ok ? null : resultado.erro.geral)
  }

  return (
    <section className="categorias">
      <h1>Categorias</h1>
      <FormularioNova cores={cores} criar={criar} />
      <AvisoFormulario mensagem={erroCarregar ?? erroExcluir} />
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
              atualizar={atualizar}
              aoExcluir={aoExcluir}
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

function LinhaCategoria({ categoria, cor, cores, atualizar, aoExcluir }) {
  const [editando, setEditando] = useState(false)
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
          onClick={() => aoExcluir(categoria)}
        >
          Excluir
        </button>
      </div>
    </li>
  )
}
