import { useState } from 'react'
import AvisoFormulario from '../../components/AvisoFormulario.jsx'
import CampoSelecao from '../../components/CampoSelecao.jsx'
import CampoTexto from '../../components/CampoTexto.jsx'
import { useCategorias } from '../../hooks/useCategorias.js'
import { useFixos } from '../../hooks/useFixos.js'
import { formatarMoeda, paraValorDaApi, paraValorDigitado } from '../../utils/formatacao.js'

const SEM_ERROS = { campos: {}, geral: null }

// "2026-11" → "11/2026"
const rotuloDoMes = (mesAno) => `${mesAno.slice(5, 7)}/${mesAno.slice(0, 4)}`

function periodo(fixo) {
  const inicio = rotuloDoMes(fixo.inicio)
  return fixo.fim ? `de ${inicio} a ${rotuloDoMes(fixo.fim)}` : `desde ${inicio}`
}

function mesDeHoje() {
  const hoje = new Date()
  return `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}`
}

// Tela "Gastos fixos" (US-07b; specs/010-gastos-fixos/contracts/tela-fixos.md).
export default function Fixos() {
  const { fixos, formas, carregando, erroCarregar, criar, atualizar, excluir } = useFixos()
  const { categorias } = useCategorias()
  const [emEdicao, setEmEdicao] = useState(null)
  const [aviso, setAviso] = useState(null)
  const nomeCategoria = Object.fromEntries(categorias.map((item) => [item.id, item.nome]))

  const avisar = (tipo, mensagem) => setAviso(mensagem ? { tipo, mensagem } : null)

  async function aoSalvar(dados) {
    avisar()
    const resultado = emEdicao ? await atualizar(emEdicao.id, dados) : await criar(dados)
    if (resultado.ok) {
      avisar('sucesso', emEdicao ? 'Gasto fixo atualizado.' : 'Gasto fixo cadastrado.')
      setEmEdicao(null)
    }
    return resultado
  }

  async function aoAlternarAtivo(fixo) {
    avisar()
    const resultado = await atualizar(fixo.id, { ativo: !fixo.ativo })
    if (resultado.ok) {
      avisar('sucesso', fixo.ativo ? 'Gasto fixo desativado.' : 'Gasto fixo reativado.')
    } else {
      avisar('erro', resultado.erro.geral)
    }
  }

  async function aoExcluir(fixo) {
    const pergunta = `Excluir o gasto fixo "${fixo.descricao}"? Os gastos já lançados continuam.`
    if (!window.confirm(pergunta)) return
    avisar()
    const resultado = await excluir(fixo.id)
    if (resultado.ok) {
      avisar('sucesso', 'Gasto fixo excluído.')
      if (emEdicao?.id === fixo.id) setEmEdicao(null)
    } else {
      avisar('erro', resultado.erro.geral)
    }
  }

  return (
    <section className="pagina-fixos">
      <h1>Gastos fixos</h1>
      <p>Os gastos fixos ativos entram sozinhos em cada mês novo.</p>
      <AvisoFormulario mensagem={erroCarregar} />
      <AvisoFormulario mensagem={aviso?.mensagem} tipo={aviso?.tipo} />
      <FormularioFixo
        key={emEdicao?.id ?? 'novo'}
        fixo={emEdicao}
        categorias={categorias}
        formas={formas}
        salvar={aoSalvar}
        aoCancelar={() => setEmEdicao(null)}
      />
      {carregando ? (
        <p>Carregando gastos fixos…</p>
      ) : fixos.length === 0 ? (
        !erroCarregar && <p>Nenhum gasto fixo. Cadastre o primeiro acima.</p>
      ) : (
        <ul className="lista-fixos">
          {fixos.map((fixo) => (
            <li key={fixo.id} className={`linha-fixo${fixo.ativo ? '' : ' inativo'}`}>
              <div className="dados-fixo">
                <strong>{fixo.descricao}</strong>
                <span>{formatarMoeda(fixo.valor)}</span>
                <span>dia {fixo.dia_vencimento}</span>
                <span>{nomeCategoria[fixo.categoria] ?? '—'}</span>
                <span>{periodo(fixo)}</span>
                {!fixo.ativo && <span className="marca-inativo">Inativo</span>}
              </div>
              <div className="acoes">
                <button
                  type="button"
                  className="secundario"
                  aria-label={`Editar ${fixo.descricao}`}
                  onClick={() => setEmEdicao(fixo)}
                >
                  Editar
                </button>
                <button
                  type="button"
                  className="secundario"
                  aria-label={`${fixo.ativo ? 'Desativar' : 'Reativar'} ${fixo.descricao}`}
                  onClick={() => aoAlternarAtivo(fixo)}
                >
                  {fixo.ativo ? 'Desativar' : 'Reativar'}
                </button>
                <button
                  type="button"
                  className="secundario"
                  aria-label={`Excluir ${fixo.descricao}`}
                  onClick={() => aoExcluir(fixo)}
                >
                  Excluir
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function FormularioFixo({ fixo, categorias, formas, salvar, aoCancelar }) {
  const editando = Boolean(fixo)
  const [descricao, setDescricao] = useState(fixo?.descricao ?? '')
  const [valor, setValor] = useState(fixo ? paraValorDigitado(fixo.valor) : '')
  const [dia, setDia] = useState(fixo ? String(fixo.dia_vencimento) : '')
  const [categoria, setCategoria] = useState(fixo ? String(fixo.categoria) : '')
  const [forma, setForma] = useState(fixo?.forma_pagamento ?? '')
  const [inicio, setInicio] = useState(fixo?.inicio ?? mesDeHoje())
  const [fim, setFim] = useState(fixo?.fim ?? '')
  const [erro, setErro] = useState(SEM_ERROS)
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    if (enviando) return
    setEnviando(true)
    setErro(SEM_ERROS)
    const resultado = await salvar({
      descricao,
      valor: paraValorDaApi(valor),
      dia_vencimento: dia === '' ? null : Number(dia),
      categoria: categoria ? Number(categoria) : null,
      forma_pagamento: forma,
      inicio,
      fim: fim || null,
    })
    setEnviando(false)
    if (!resultado.ok) {
      setErro(resultado.erro)
    } else if (!editando) {
      // Cadastrado: o formulário volta ao vazio para o próximo.
      setDescricao('')
      setValor('')
      setDia('')
      setCategoria('')
      setForma('')
      setInicio(mesDeHoje())
      setFim('')
    }
  }

  const titulo = editando ? 'Editar gasto fixo' : 'Novo gasto fixo'
  const rotuloBotao = editando
    ? enviando
      ? 'Salvando…'
      : 'Salvar alterações'
    : enviando
      ? 'Cadastrando…'
      : 'Cadastrar'

  return (
    <form className="cartao formulario-gasto" aria-label={titulo} onSubmit={aoEnviar} noValidate>
      <h2>{titulo}</h2>
      <AvisoFormulario mensagem={erro.geral} />
      <fieldset>
        <CampoTexto
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
          rotulo="Dia de vencimento"
          nome="dia_vencimento"
          tipo="number"
          valor={dia}
          aoMudar={setDia}
          erros={erro.campos.dia_vencimento}
          min="1"
          max="31"
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
        <CampoTexto
          rotulo="Início"
          nome="inicio"
          tipo="month"
          valor={inicio}
          aoMudar={setInicio}
          erros={erro.campos.inicio}
        />
        <CampoTexto
          rotulo="Fim (opcional)"
          nome="fim"
          tipo="month"
          valor={fim}
          aoMudar={setFim}
          erros={erro.campos.fim}
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
