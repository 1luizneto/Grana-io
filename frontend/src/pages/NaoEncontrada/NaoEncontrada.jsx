import { Link } from 'react-router'

// Endereço inexistente (FR-018), com ou sem sessão.
export default function NaoEncontrada() {
  return (
    <main className="pagina-acesso">
      <div className="cartao">
        <h1>Página não encontrada.</h1>
        <p>
          <Link to="/">Voltar ao início</Link>
        </p>
      </div>
    </main>
  )
}
