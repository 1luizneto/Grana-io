import { Route, Routes } from 'react-router'
import Entrar from './pages/Entrar/Entrar.jsx'
import Inicio from './pages/Inicio/Inicio.jsx'

// Rotas da interface (specs/005-telas-login-cadastro/contracts/interface.md).
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Inicio />} />
      <Route path="/entrar" element={<Entrar />} />
    </Routes>
  )
}
