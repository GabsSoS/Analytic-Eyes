import { Routes, Route } from 'react-router-dom'
import Layout from './pages/Layout/Layout'
import Login from './pages/Login/Login'
import Home from './pages/Home/Home'
import Criar from './pages/Criar/Fluxos'
import Fluxos from './pages/Details/Details'
import Settings from './pages/Settings/Settings'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route element={<Layout />}>
        <Route path="/home" element={<Home />} />
        <Route path="/Criar" element={<Criar />} />
        <Route path="/Fluxos" element={<Fluxos />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App