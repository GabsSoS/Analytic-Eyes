import Logo from "../assets/components/Logo 2.png"
import Lupa  from "../assets/components/Lupa.png"
import Info from "../assets/components/Info App.png"
import { Link } from 'react-router-dom'
import './Header.css'

function Header() {
  
  return (
    <nav className="Cabeçalho">
      <img src={Logo} alt="Analitical Eyes" />
      <div className="barra-de-pesquisa">
        <img className="img-lupa" src={Lupa} alt="Lupa" />
        <input className="texto-pesquisa" type="search" placeholder="Procure por recursos úteis" />
      </div>
      <img className="infoapp" src={Info} alt="Informações do app" />
    </nav>
  )
}

export default Header
