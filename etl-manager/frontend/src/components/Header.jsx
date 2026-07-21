import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "./Header.css";

const TELAS = [
  { label: "Início", path: "/home" },
  { label: "Criar Fluxo", path: "/criar" },
  { label: "Fluxos", path: "/fluxos" },
  { label: "Configurações", path: "/settings" },
];

function Header() {
  const navigate = useNavigate();
  const wrapperRef = useRef(null);
  const [query, setQuery] = useState("");
  const [pipelines, setPipelines] = useState([]);
  const [loading, setLoading] = useState(false);
  const [aberto, setAberto] = useState(false);
  const username = localStorage.getItem("username") || "";
  const initial = username ? username.charAt(0).toUpperCase() : "?";

  const telasFiltradas = TELAS.filter((t) =>
    t.label.toLowerCase().includes(query.toLowerCase())
  );

  const temResultados = telasFiltradas.length > 0 || pipelines.length > 0;

  useEffect(() => {
    if (!query.trim()) {
      setPipelines([]);
      return;
    }

    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const res = await api.get("pipelines/");
        const todos = res.data?.pipelines ?? [];
        const filtrados = todos
          .filter((p) => p.name?.toLowerCase().includes(query.toLowerCase()))
          .slice(0, 6);
        setPipelines(filtrados);
      } catch {
        setPipelines([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      clearTimeout(timer);
      setLoading(false);
    };
  }, [query]);

  useEffect(() => {
    const onClickFora = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setAberto(false);
      }
    };
    document.addEventListener("mousedown", onClickFora);
    return () => document.removeEventListener("mousedown", onClickFora);
  }, []);

  const selecionar = (path) => {
    navigate(path);
    setQuery("");
    setAberto(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Escape") {
      setAberto(false);
      e.target.blur();
    }
  };

  return (
    <header className="app-header">
      <button
        type="button"
        className="app-header-brand"
        onClick={() => navigate("/home")}
      >
        <span className="app-header-logo" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M2 12c2.5-5 6.5-8 10-8s7.5 3 10 8c-2.5 5-6.5 8-10 8s-7.5-3-10-8Z"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinejoin="round"
            />
            <circle cx="12" cy="12" r="3.4" fill="currentColor" />
          </svg>
        </span>
        <span className="app-header-title">Analytic Eyes</span>
      </button>

      <div className="app-header-search" ref={wrapperRef}>
        <svg className="app-header-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="11" cy="11" r="7" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        <input
          className="app-header-search-input"
          type="search"
          placeholder="Procure por fluxos ou telas..."
          value={query}
          autoComplete="off"
          onChange={(e) => {
            setQuery(e.target.value);
            setAberto(true);
          }}
          onFocus={() => query && setAberto(true)}
          onKeyDown={handleKeyDown}
        />

        {aberto && query.trim() && (
          <div className="search-dropdown">
            {telasFiltradas.length > 0 && (
              <div className="search-group">
                <span className="search-group-label">Telas</span>
                {telasFiltradas.map((tela) => (
                  <button
                    key={tela.path}
                    type="button"
                    className="search-item"
                    onClick={() => selecionar(tela.path)}
                  >
                    <svg className="search-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="3" width="18" height="18" rx="2" />
                      <path d="M3 9h18" />
                    </svg>
                    {tela.label}
                  </button>
                ))}
              </div>
            )}

            {(loading || pipelines.length > 0) && (
              <div className="search-group">
                <span className="search-group-label">Fluxos</span>
                {loading ? (
                  <div className="search-loading">Buscando...</div>
                ) : (
                  pipelines.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      className="search-item"
                      onClick={() => selecionar(`/Details/${p.id}`)}
                    >
                      <svg className="search-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                      </svg>
                      {p.name}
                    </button>
                  ))
                )}
              </div>
            )}

            {!loading && !temResultados && (
              <div className="search-empty">Nenhum resultado encontrado</div>
            )}
          </div>
        )}
      </div>

      <div className="app-header-actions">
        <button
          type="button"
          className="app-header-icon-btn"
          aria-label="Ajuda"
          title="Ajuda"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="9" />
            <path d="M9.5 9a2.5 2.5 0 1 1 3.4 2.32c-.72.3-1.4.9-1.4 1.68v.3" />
            <path d="M12 17h.01" />
          </svg>
        </button>

        <button
          type="button"
          className="app-header-avatar"
          onClick={() => navigate("/settings")}
          title={username || "Conta"}
        >
          {initial}
        </button>
      </div>
    </header>
  );
}

export default Header;
