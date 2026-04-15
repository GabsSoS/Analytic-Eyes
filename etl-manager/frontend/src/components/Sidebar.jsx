import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import Menu from "../assets/components/Menu.png";
import HomeAtiva from "../assets/components/Home Ativa.png";
import HomeInativa from "../assets/components/Home Desativada.png";
import CriarAtivo from "../assets/components/Criar Ativa.png";
import CriarDesativado from "../assets/components/Criar Desativada.png";
import FluxoAtivo from "../assets/components/Fluxos Ativa.png";
import FluxoDesativado from "../assets/components/Fluxos Desativada.png";
import SettingsAtiva from "../assets/components/Settings Ativa.png";
import SettingsDesativado from "../assets/components/Settings Desativada.png";

import "./Sidebar.css";

function Sidebar() {
  const [isActive, setIsActive] = useState(true);
  const location = useLocation();
  const currentPath = location.pathname;

  const toggleSidebar = () => {
    const newState = !isActive;
    setIsActive(newState);
    // Aumenta o padding quando o sidebar recolhe
    const paddingValue = newState ? "3.125vw" : "9.50vw";
    document.documentElement.style.setProperty("--sidebar-padding", paddingValue);
  };

  const isCurrentPage = (path) => currentPath === path;
  const isCriarSection = currentPath === "/criar" || currentPath.startsWith("/editar/");
  const isFluxosSection = currentPath === "/fluxos" || currentPath.startsWith("/Details/");

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

          <li className={`container-li ${isCriarSection ? "active-link" : ""}`}>
            <Link to="/criar">
              <img
                src={isCriarSection ? CriarAtivo  : CriarDesativado}
                alt="Criar"
              />
              <span>Criar</span>
            </Link>
          </li>
          <li className={`container-li ${isFluxosSection ? "active-link" : ""}`}>
            <Link to="/fluxos">
              <img
                src={isFluxosSection ? FluxoAtivo : FluxoDesativado}
                alt="/fluxos"
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
              <span>Configurações</span>
            </Link>
          </li>
        </ul>
      </nav>
    </aside>
  );
}

export default Sidebar;
