import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Home.css";
import api from "../../services/api";

const STATUS_ROWS = [
  { key: "NOT_RUN", label: "Não executados", tone: "idle" },
  { key: "PENDING", label: "Pendentes", tone: "warning" },
  { key: "RUNNING", label: "Em execução", tone: "info" },
  { key: "SUCCESS", label: "Sucesso", tone: "success" },
  { key: "FAILED", label: "Falha", tone: "danger" },
];

function Home() {
  const navigate = useNavigate();
  const username = localStorage.getItem("username") || "";
  const [stats, setStats] = useState({
    total_visible: 0,
    owned_count: 0,
    shared_count: 0,
    status_counts: {},
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function loadStats() {
      try {
        const res = await api.get("pipelines/stats/");
        if (!mounted) return;
        setStats(res.data);
      } catch (err) {
        console.error("Erro ao carregar estatísticas:", err?.response?.data || err.message || err);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadStats();
    return () => {
      mounted = false;
    };
  }, []);

  const statusCounts = stats.status_counts || {};
  const maxCount = Math.max(...STATUS_ROWS.map((row) => Number(statusCounts[row.key] || 0)), 1);

  return (
    <div className="home-page">
      <section className="home-hero">
        <div className="home-hero-pattern" aria-hidden="true" />
        <div className="home-hero-content">
          <span className="home-hero-eyebrow">Analytic Eyes</span>
          <h1>Orquestrar fluxos e automações nunca foi tão fácil</h1>
          <p>
            {username ? `Bem-vindo(a), ${username}. ` : ""}
            Maximize a produtividade e simplifique a administração sem
            comprometer o gerenciamento e a segurança dos seus dados.
          </p>
          <div className="home-hero-actions">
            <button type="button" className="home-btn primary" onClick={() => navigate("/criar")}>
              Criar novo fluxo
            </button>
            <button type="button" className="home-btn ghost" onClick={() => navigate("/fluxos")}>
              Ver todos os fluxos
            </button>
          </div>
        </div>
      </section>

      <section className="home-stats">
        <div className="home-stat-card">
          <span className="home-stat-icon total" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="4" width="7" height="6" rx="1.5" />
              <rect x="14" y="4" width="7" height="6" rx="1.5" />
              <rect x="8.5" y="14" width="7" height="6" rx="1.5" />
              <path d="M6.5 10v2a2 2 0 0 0 2 2h1M17.5 10v2a2 2 0 0 1-2 2h-1" />
            </svg>
          </span>
          <div>
            <span className="home-stat-value">{loading ? "—" : stats.total_visible}</span>
            <span className="home-stat-label">Fluxos visíveis</span>
          </div>
        </div>

        <div className="home-stat-card">
          <span className="home-stat-icon owned" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="8" r="3.6" />
              <path d="M4.5 20c1.4-3.6 4.4-5.6 7.5-5.6s6.1 2 7.5 5.6" />
            </svg>
          </span>
          <div>
            <span className="home-stat-value">{loading ? "—" : stats.owned_count}</span>
            <span className="home-stat-label">Criados por você</span>
          </div>
        </div>

        <div className="home-stat-card">
          <span className="home-stat-icon shared" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="7" cy="12" r="2.6" />
              <circle cx="17" cy="6" r="2.6" />
              <circle cx="17" cy="18" r="2.6" />
              <path d="M9.3 10.7 14.7 7.3M9.3 13.3l5.4 3.4" />
            </svg>
          </span>
          <div>
            <span className="home-stat-value">{loading ? "—" : stats.shared_count}</span>
            <span className="home-stat-label">Compartilhados com você</span>
          </div>
        </div>
      </section>

      <section className="home-columns">
        <div className="home-card">
          <div className="home-card-header">
            <h2>Status dos fluxos</h2>
            <span className="home-card-sub">Conta atual: Ativo</span>
          </div>

          <div className="home-status-list">
            {STATUS_ROWS.map((row) => {
              const count = Number(statusCounts[row.key] || 0);
              const pct = Math.round((count / maxCount) * 100);
              return (
                <div className="home-status-row" key={row.key}>
                  <span className={`home-status-dot ${row.tone}`} aria-hidden="true" />
                  <span className="home-status-label">{row.label}</span>
                  <span className="home-status-track">
                    <span
                      className={`home-status-fill ${row.tone}`}
                      style={{ width: `${count ? Math.max(pct, 6) : 0}%` }}
                    />
                  </span>
                  <span className="home-status-count">{count}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="home-card">
          <div className="home-card-header">
            <h2>Destaques</h2>
          </div>

          <div className="home-highlights">
            <div className="home-highlight">
              <span className="home-highlight-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 18h6M10 21h4" />
                  <path d="M12 3a6 6 0 0 0-3.6 10.8c.5.4.8 1 .8 1.6v.1h5.6v-.1c0-.6.3-1.2.8-1.6A6 6 0 0 0 12 3Z" />
                </svg>
              </span>
              <div className="home-highlight-text">
                <strong>Novas atualizações mensais no sistema</strong>
                <p>
                  O sistema de orquestração de fluxos foi atualizado com
                  melhorias que incluem monitoramento em tempo real,
                  centralização de logs e integração simplificada com
                  serviços de nuvem.
                </p>
              </div>
            </div>

            <div className="home-highlight">
              <span className="home-highlight-icon alt" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="8.5" />
                  <path d="M12 7.5V12l3 2" />
                </svg>
              </span>
              <div className="home-highlight-text">
                <strong>Aumente a produtividade com ETLs agendados</strong>
                <p>
                  Permita que processos de integração e transformação de
                  dados sejam executados automaticamente nos horários
                  definidos, sem intervenção manual.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
