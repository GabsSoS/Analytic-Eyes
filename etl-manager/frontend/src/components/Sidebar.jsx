import { Link, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import Menu from "../assets/components/Menu.png";
import HomeAtiva from "../assets/components/home Ativa.png";
import HomeInativa from "../assets/components/home Desativada.png";
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
  const navigate = useNavigate();
  const currentPath = location.pathname;

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login");
  };

  const toggleSidebar = () => {
    const newState = !isActive;
    setIsActive(newState);
    // Ajusta o espaçamento quando a barra lateral é recolhida
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
          alt="Recolher menu"
          className="icons"
          onClick={toggleSidebar}
        />
        <ul>
          <li className={`container-li ${isCurrentPage("/home") ? "active-link" : ""}`}>
            <Link to="/home">
              <img
                src={isCurrentPage("/home") ? HomeAtiva : HomeInativa}
                alt="Início"
                className="icons-final"
              />
              <span>Início</span>
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
                alt="Fluxos"
              />
              <span>Fluxos</span>
            </Link>
          </li>
          <li className={`container-li ${isCurrentPage("/settings") ? "active-link" : ""}`}>
            <Link to="/settings">
              <img
                src={isCurrentPage("/settings") ? SettingsAtiva : SettingsDesativado}
                alt="Configurações"
              />
              <span>Configurações</span>
            </Link>
          </li>
          <li className="container-li container-li-logout">
            <button className="sidebar-logout-btn" onClick={handleLogout} type="button">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="sidebar-logout-icon"
              >
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              <span>Sair</span>
            </button>
          </li>
        </ul>
      </nav>
    </aside>
  );
}

export default Sidebar;
