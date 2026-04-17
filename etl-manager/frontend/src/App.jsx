import { Routes, Route } from 'react-router-dom'
import Layout from './pages/Layout/Layout'
import Login from './pages/Login/Login'
import Home from './pages/Home/Home'
import Criar from './pages/Criar/Fluxos'
import Fluxos from './pages/Fluxos/Listagem'
import Details from './pages/Details/Details'
import Settings from './pages/Settings/Settings'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/login" element={<Login />} />
      <Route element={<Layout />}>
        <Route path="/home" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/criar" element={<ProtectedRoute><Criar /></ProtectedRoute>} />
        <Route path="/editar/:id" element={<ProtectedRoute><Criar /></ProtectedRoute>} />
        <Route path="/fluxos" element={<ProtectedRoute><Fluxos /></ProtectedRoute>} />
        <Route path="/Details/:id" element={<ProtectedRoute><Details /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      </Route>
      
    </Routes>
  )
}

export default App
