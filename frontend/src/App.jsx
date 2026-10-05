import { Route, Routes } from 'react-router'
import RotaProtegida from './auth/RotaProtegida.jsx'
import RotaPublica from './auth/RotaPublica.jsx'
import Layout from './components/Layout.jsx'
import Rodape from './components/Rodape.jsx'
import Cadastro from './pages/Cadastro/Cadastro.jsx'
import Entrar from './pages/Entrar/Entrar.jsx'
import Inicio from './pages/Inicio/Inicio.jsx'
import NaoEncontrada from './pages/NaoEncontrada/NaoEncontrada.jsx'

// Rotas da interface (specs/005-telas-login-cadastro/contracts/interface.md). As telas protegidas
// das próximas USs entram como filhas do Layout, atrás da RotaProtegida.
export default function App() {
  return (
    <>
      <Routes>
        <Route element={<RotaProtegida />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Inicio />} />
          </Route>
        </Route>
        <Route element={<RotaPublica />}>
          <Route path="/entrar" element={<Entrar />} />
          <Route path="/cadastro" element={<Cadastro />} />
        </Route>
        <Route path="*" element={<NaoEncontrada />} />
      </Routes>
      {/* Fora das rotas: a verificação de saúde roda uma vez por carregamento. */}
      <Rodape />
    </>
  )
}
