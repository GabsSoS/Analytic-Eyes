import { Routes, Route } from 'react-router-dom'
import Layout from './pages/Layout/Layout'
import Login from './pages/Login/Login'
import Home from './pages/Home/Home'
import Fluxos from './pages/Fluxos/Fluxos'
import Details from './pages/Details/Details'
import Settings from './pages/Settings/Settings'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route element={<Layout />}>
        <Route path="/home" element={<Home />} />
        <Route path="/fluxos" element={<Fluxos />} />
        <Route path="/details" element={<Details />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App