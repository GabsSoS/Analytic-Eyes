import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Logo from "../assets/components/Logo 4.png";
import Lupa from "../assets/components/Lupa.png";
import Info from "../assets/components/Info App.png";
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
    <nav className="Cabeçalho">
      <img src={Logo} alt="Analitical Eyes" />

      <div className="barra-de-pesquisa" ref={wrapperRef}>
        <img className="img-lupa" src={Lupa} alt="Lupa" />
        <input
          className="texto-pesquisa"
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

      <img className="infoapp" src={Info} alt="Informações do app" />
    </nav>
  );
}

export default Header;
