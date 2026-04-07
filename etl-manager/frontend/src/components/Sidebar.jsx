import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import Menu from "../assets/components/Menu.png";
import HomeAtiva from "../assets/components/Home Ativa.png";
import HomeInativa from "../assets/components/Home Desativada.png";
import CriarAtivo from "../assets/components/Criar Ativa.png";
import CriarDesativado from "../assets/components/Criar Desativada.png";
import FluxoAtivo from "../assets/components/Fluxos Ativa.png";
import FluxoDesativado from "../assets/components/Fluxos Desativada.png";
import SettingsAtiva from "../assets/components/Settings Ativa.png"
import SettingsDesativado from "../assets/components/Settings Desativada.png";

import "./Sidebar.css";

function Sidebar() {
  const [isActive, setIsActive] = useState(true);
  const location = useLocation();

  const toggleSidebar = () => {
    setIsActive(!isActive);
  };



  const isCurrentPage = (path) => location.pathname === path;

  return (
    <aside className={isActive ? "active" : "deactivate"}>
      <nav className="sidebar">
        <img
          src={Menu}
          alt="Recolher Menu"
          className="icons"
          onClick={toggleSidebar}
        />
        <ul>
          <li className={`container-li ${isCurrentPage("/home") ? "active-link" : ""}`}>
            <Link to="/home">
              <img
                src={isCurrentPage("/home") ? HomeAtiva : HomeInativa}
                alt="Home"
                className="icons-final"
              />
              <span>Home</span>
            </Link>
          </li>

          <li className={`container-li ${isCurrentPage("/fluxos") ? "active-link" : ""}`}>
            <Link to="/fluxos">
              <img
                src={isCurrentPage("/fluxos") ? CriarAtivo  : CriarDesativado}
                alt="Fluxos"
                
              />
              <span>Criar</span>
            </Link>
          </li>
          <li className={`container-li ${isCurrentPage("/details") ? "active-link" : ""}`}>
            <Link to="/Fluxos">
              <img
                src={isCurrentPage("/Fluxos") ? FluxoAtivo : FluxoDesativado}
                alt="/Fluxos"
                
              />
              <span>Fluxos</span>
            </Link>
          </li>
          <li className={`container-li ${isCurrentPage("/settings") ? "active-link" : ""}`}>
            <Link to="/settings">
                <img
                src={isCurrentPage("/settings") ? SettingsAtiva : SettingsDesativado}
                alt="/settings"
                
              />
              <span>Settings</span>
            </Link>
          </li>
        </ul>
      </nav>
    </aside>
  );
}

export default Sidebar;