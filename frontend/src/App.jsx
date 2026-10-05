import { Route, Routes } from 'react-router'
import Inicio from './pages/Inicio/Inicio.jsx'

// Rotas da interface (specs/005-telas-login-cadastro/contracts/interface.md).
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Inicio />} />
    </Routes>
  )
}
