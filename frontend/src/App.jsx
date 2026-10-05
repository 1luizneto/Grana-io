import { Route, Routes } from 'react-router'
import RotaProtegida from './auth/RotaProtegida.jsx'
import RotaPublica from './auth/RotaPublica.jsx'
import Entrar from './pages/Entrar/Entrar.jsx'
import Inicio from './pages/Inicio/Inicio.jsx'

// Rotas da interface (specs/005-telas-login-cadastro/contracts/interface.md). As telas protegidas
// das próximas USs entram como filhas da RotaProtegida.
export default function App() {
  return (
    <Routes>
      <Route element={<RotaProtegida />}>
        <Route path="/" element={<Inicio />} />
      </Route>
      <Route element={<RotaPublica />}>
        <Route path="/entrar" element={<Entrar />} />
      </Route>
    </Routes>
  )
}
