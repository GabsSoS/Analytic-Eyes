import { Link, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import "./Sidebar.css";

const NAV_ICONS = {
  home: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5.5 9.8V19a1 1 0 0 0 1 1H9a1 1 0 0 0 1-1v-4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v4a1 1 0 0 0 1 1h2.5a1 1 0 0 0 1-1V9.8" />
    </svg>
  ),
  criar: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v8M8 12h8" />
    </svg>
  ),
  fluxos: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="7" height="6" rx="1.5" />
      <rect x="14" y="4" width="7" height="6" rx="1.5" />
      <rect x="8.5" y="14" width="7" height="6" rx="1.5" />
      <path d="M6.5 10v2a2 2 0 0 0 2 2h1M17.5 10v2a2 2 0 0 1-2 2h-1" />
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3.2" />
      <path d="M4.6 9.4A2.6 2.6 0 0 1 9.4 4.6l.3.52a2.6 2.6 0 0 0 4.6 0l.3-.52a2.6 2.6 0 0 1 4.8 4.8l-.52.3a2.6 2.6 0 0 0 0 4.6l.52.3a2.6 2.6 0 0 1-4.8 4.8l-.3-.52a2.6 2.6 0 0 0-4.6 0l-.3.52a2.6 2.6 0 0 1-4.8-4.8l.52-.3a2.6 2.6 0 0 0 0-4.6l-.52-.3Z" />
    </svg>
  ),
};

const NAV_ITEMS = [
  { key: "home", label: "Início", path: "/home" },
  { key: "criar", label: "Criar", path: "/criar" },
  { key: "fluxos", label: "Fluxos", path: "/fluxos" },
  { key: "settings", label: "Configurações", path: "/settings" },
];

function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const currentPath = location.pathname;

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    navigate("/login");
  };

  const toggleSidebar = () => {
    const next = !collapsed;
    setCollapsed(next);
    document.documentElement.style.setProperty(
      "--sidebar-w",
      next ? "var(--sidebar-w-collapsed)" : "240px"
    );
  };

  const isActive = (item) => {
    if (item.key === "criar") {
      return currentPath === "/criar" || currentPath.startsWith("/editar/");
    }
    if (item.key === "fluxos") {
      return currentPath === "/fluxos" || currentPath.startsWith("/Details/");
    }
    return currentPath === item.path;
  };

  return (
    <aside className={`app-sidebar ${collapsed ? "collapsed" : ""}`}>
      <button
        type="button"
        className="app-sidebar-toggle"
        onClick={toggleSidebar}
        aria-label={collapsed ? "Expandir menu" : "Recolher menu"}
        title={collapsed ? "Expandir menu" : "Recolher menu"}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          {collapsed ? <path d="m9 6 6 6-6 6" /> : <path d="m15 6-6 6 6 6" />}
        </svg>
      </button>

      <nav className="app-sidebar-nav">
        <ul>
          {NAV_ITEMS.map((item) => {
            const active = isActive(item);
            return (
              <li key={item.key} className={`app-sidebar-item ${active ? "active" : ""}`}>
                <Link to={item.path} title={collapsed ? item.label : undefined}>
                  <span className="app-sidebar-icon">{NAV_ICONS[item.key]}</span>
                  <span className="app-sidebar-label">{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="app-sidebar-footer">
          <button
            className="app-sidebar-logout"
            onClick={handleLogout}
            type="button"
            title={collapsed ? "Sair" : undefined}
          >
            <span className="app-sidebar-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </span>
            <span className="app-sidebar-label">Sair</span>
          </button>
        </div>
      </nav>
    </aside>
  );
}

export default Sidebar;
