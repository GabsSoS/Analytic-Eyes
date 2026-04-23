
import React, { useEffect, useState } from 'react';
import './Home.css';
import IdeaIcon from "../../assets/Home/Idea.png";
import DevicesIcon from "../../assets/Home/Device.png";
import api from '../../services/api';

const Illustration = () => (
  <svg width="420" height="260" viewBox="0 0 420 260" fill="none" xmlns="http://www.w3.org/2000/svg" className="hero-illustration">
    <rect x="30" y="20" width="300" height="200" rx="12" fill="#e6f3ff" stroke="#d7ecff" />
    <rect x="50" y="36" width="260" height="140" rx="8" fill="#ffffff"/>
    <g transform="translate(60,56)">
      <rect x="0" y="0" width="220" height="12" rx="6" fill="#f1f5f9"/>
      <rect x="0" y="28" width="36" height="8" rx="4" fill="#dbeafe"/>
      <rect x="48" y="28" width="140" height="8" rx="4" fill="#dbeafe"/>
      <circle cx="180" cy="24" r="16" fill="#cdeffd"/>
      <path d="M10 80 L50 50 L90 72 L130 40 L170 60" stroke="#60a5fa" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
    </g>
    <rect x="170" y="230" width="120" height="8" rx="4" fill="#111827" opacity="0.08"/>
  </svg>
);

function Home() {
  const [stats, setStats] = useState({
    total_visible: 0,
    owned_count: 0,
    shared_count: 0,
    status_counts: {},
  });

  useEffect(() => {
    let mounted = true;
    async function loadStats() {
      try {
        const res = await api.get('pipelines/stats/');
        if (!mounted) return;
        setStats(res.data);
      } catch (err) {
        console.error('Erro ao carregar estatísticas:', err?.response?.data || err.message || err);
      }
    }

    loadStats();
    return () => { mounted = false; };
  }, []);

  const statusCounts = stats.status_counts || {};
  const maxCount = Math.max(...Object.values(statusCounts).map(n => Number(n || 0)), 1);

  const getHeight = (count) => {
    const n = Number(count || 0);
    return `${Math.round((n / maxCount) * 60) + 12}px`;
  };

  return (
    <div className="home-page">
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">Orquestrar fluxos e automações nunca foi tão fácil</h1>
          <p className="hero-sub">Maximize a produtividade e simplifique a administração sem comprometer o gerenciamento e a segurança</p>
        </div>

        <div className="hero-art">
          <Illustration />
        </div>
      </section>

      <section className="cards">
        <div className="card status-card">
          <h3 className="card-title">Status</h3>
          <div className="status-body">
              <div className="status-left">
                <div className="status-meta">Fluxos criados</div>
                <div className="status-number">{stats.owned_count}</div>
                <div className="status-small">Visíveis: {stats.total_visible} · Compartilhadas: {stats.shared_count}</div>
              </div>
              <div className="status-bars">
                <div className="bar" style={{ height: getHeight(statusCounts.NOT_RUN), background: '#e5e7eb' }} title={`Não executados: ${statusCounts.NOT_RUN || 0}`}></div>
                <div className="bar" style={{ height: getHeight(statusCounts.PENDING), background: '#f59e0b' }} title={`Pendente: ${statusCounts.PENDING || 0}`}></div>
                <div className="bar" style={{ height: getHeight(statusCounts.RUNNING), background: '#60a5fa' }} title={`Em execução: ${statusCounts.RUNNING || 0}`}></div>
                <div className="bar" style={{ height: getHeight(statusCounts.SUCCESS), background: '#10b981' }} title={`Sucesso: ${statusCounts.SUCCESS || 0}`}></div>
                <div className="bar" style={{ height: getHeight(statusCounts.FAILED), background: '#ef4444' }} title={`Falha: ${statusCounts.FAILED || 0}`}></div>
              </div>
          </div>

          <div className="account">
            <div className="account-label">Status da conta</div>
            <div className="account-value">Ativo</div>
          </div>
        </div>

        <div className="card highlights-card">
          <h3 className="card-title">Destaques</h3>
          <div className="highlights">
            <div className="highlight">
                <div className="icon"><img src={IdeaIcon} alt="Ideia" /></div>
              <div className="highlight-text">
                <strong>Novas atualizações mensais no sistema</strong>
                <p>O sistema de orquestração de fluxos foi atualizado com melhorias que incluem monitoramento em tempo real, centralização de logs e integração simplificada com serviços de nuvem.</p>
              </div>
            </div>

            <div className="highlight">
              <div className="icon"><img src={DevicesIcon} alt="Dispositivos" /></div>
              <div className="highlight-text">
                <strong>Aumente a produtividade com ETLs agendados</strong>
                <p>Aumente a produtividade com ETLs agendados, permitindo que processos de integração e transformação de dados sejam executados automaticamente nos horários definidos.</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;