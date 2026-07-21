import "./Listagem.css";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";

const FLUXOS_MOCKADOS = [
  { id: 1, nome: "OP - Abertura do dia", ultimaExecucao: "Há 1 hora", proprietario: "Lucas Souza" },
  { id: 2, nome: "Limpeza de tabela", ultimaExecucao: "4 semanas", proprietario: "Lucas Souza" },
  { id: 3, nome: "Limpeza planilhas ETL", ultimaExecucao: "2 dias", proprietario: "Lucas Souza" },
  { id: 4, nome: "Softwares sem licenca ETL", ultimaExecucao: "Há 10 minutos", proprietario: "Lucas Souza" },
  { id: 5, nome: "Carga clientes ativos ETL", ultimaExecucao: "1 mês", proprietario: "Lucas Souza" },
  { id: 6, nome: "Normalizacao enderecos ETL", ultimaExecucao: "Há 5 horas", proprietario: "Lucas Souza" },
  { id: 7, nome: "Inventario servidores ETL", ultimaExecucao: "Há 1 ano", proprietario: "Lucas Souza" },
  { id: 8, nome: "Atualizacao precos ETL", ultimaExecucao: "15 minutos", proprietario: "Ana Lima" },
  { id: 9, nome: "Consolidacao financeira ETL", ultimaExecucao: "Há 5 dias", proprietario: "Camila Rocha" },
  { id: 10, nome: "Monitoramento acessos ETL", ultimaExecucao: "Há 3 horas", proprietario: "Pedro Martins" },
  { id: 11, nome: "Validacao contratos ETL", ultimaExecucao: "Há 12 horas", proprietario: "Juliana Costa" },
  { id: 12, nome: "Integracao RH ETL", ultimaExecucao: "Há 1 hora", proprietario: "Bruno Alves" },
  { id: 13, nome: "Atualizacao do DB", ultimaExecucao: "2 semanas", proprietario: "Mariana Reis" },
];

const ABAS = {
  meus: "meus",
  compartilhados: "compartilhados",
};

const normalizarTexto = (valor) =>
  String(valor ?? "")
    .trim()
    .toLowerCase();

const formatarUltimaExecucao = (lastRun) => {
  if (!lastRun || !lastRun.started_at) {
    return "Nunca executada";
  }

  const dataExecucao = new Date(lastRun.started_at);
  const agora = new Date();
  const diffMs = agora - dataExecucao;
  const diffMin = Math.floor(diffMs / (1000 * 60));
  const diffHoras = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDias = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMin < 1) {
    return "Agora mesmo";
  } else if (diffMin < 60) {
    return `Há ${diffMin} minuto${diffMin > 1 ? 's' : ''}`;
  } else if (diffHoras < 24) {
    return `Há ${diffHoras} hora${diffHoras > 1 ? 's' : ''}`;
  } else if (diffDias < 7) {
    return `Há ${diffDias} dia${diffDias > 1 ? 's' : ''}`;
  } else if (diffDias < 30) {
    const semanas = Math.floor(diffDias / 7);
    return `Há ${semanas} semana${semanas > 1 ? 's' : ''}`;
  } else if (diffDias < 365) {
    const meses = Math.floor(diffDias / 30);
    return `Há ${meses} mês${meses > 1 ? 'es' : ''}`;
  } else {
    const anos = Math.floor(diffDias / 365);
    return `Há ${anos} ano${anos > 1 ? 's' : ''}`;
  }
};

const normalizarFluxo = (fluxo, index) => ({
  id: fluxo.id ?? `${fluxo.nome ?? fluxo.name ?? "fluxo"}-${index}`,
  nome: fluxo.nome ?? fluxo.name ?? "Fluxo sem nome",
  ultimaExecucao: formatarUltimaExecucao(fluxo.last_run),
  proprietario:
    fluxo.proprietario ??
    fluxo.owner ??
    fluxo.proprietary ??
    "Sem proprietario",
});

function Fluxos() {
  const navigate = useNavigate();
  const [abaAtiva, setAbaAtiva] = useState(ABAS.meus);
  const [fluxos, setFluxos] = useState([]);
  const [usuarioAtual, setUsuarioAtual] = useState(
    localStorage.getItem("username") || ""
  );
  const [carregando, setCarregando] = useState(false);

  useEffect(() => {
    const buscarFluxos = async () => {
      setCarregando(true);
      console.log("Iniciando busca de fluxos...");

      try {
        const response = await api.get("pipelines/");
        const payload = response.data;
        const listaRecebida = payload?.pipelines ?? [];
        console.log("Resposta da API:", payload);

        const fluxosNormalizados = Array.isArray(listaRecebida)
          ? listaRecebida.map(normalizarFluxo)
          : [];

        console.log("Fluxos recebidos da API:", listaRecebida);
        console.log("Fluxos normalizados:", fluxosNormalizados);
        setFluxos(fluxosNormalizados);

        const usuarioDaApi = payload?.current_user;
        console.log("Usuário atual da API:", usuarioDaApi);
        if (usuarioDaApi) {
          setUsuarioAtual(usuarioDaApi);
          localStorage.setItem("username", usuarioDaApi);
        }
      } catch (error) {
        console.error("Erro ao buscar fluxos:", error);
        setFluxos([]);
      } finally {
        setCarregando(false);
      }
    };

    buscarFluxos();
  }, [navigate]);

  const fluxosFiltrados = useMemo(() => {
    const usuarioNormalizado = normalizarTexto(usuarioAtual);

    return fluxos.filter((fluxo) => {
      const donoDoFluxo = normalizarTexto(fluxo.proprietario);
      const ehMeuFluxo = donoDoFluxo === usuarioNormalizado;

      return abaAtiva === ABAS.meus ? ehMeuFluxo : !ehMeuFluxo;
    });
  }, [abaAtiva, fluxos, usuarioAtual]);

  const abrirDetalhes = (fluxoId) => {
    navigate(`/Details/${fluxoId}`);
  };

  const tituloAba =
    abaAtiva === ABAS.meus
      ? "Nenhum fluxo criado por você."
      : "Nenhum fluxo compartilhado com você.";

  const iniciais = (nome) =>
    String(nome ?? "?")
      .trim()
      .charAt(0)
      .toUpperCase() || "?";

  return (
    <section className="fluxos-page">
      <div className="fluxos-shell">
        <header className="fluxos-header">
          <div>
            <h1>Fluxos</h1>
            <p className="fluxos-subtitle">Gerencie e acompanhe seus pipelines de dados</p>
          </div>
          <button type="button" className="fluxos-new-button" onClick={() => navigate("/criar")}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
            Novo fluxo
          </button>
        </header>

        <div className="fluxos-tabs" role="tablist" aria-label="Categorias de fluxos">
          <button
            type="button"
            className={`fluxos-tab ${abaAtiva === ABAS.meus ? "ativa" : ""}`}
            onClick={() => setAbaAtiva(ABAS.meus)}
          >
            Meus Fluxos
          </button>
          <button
            type="button"
            className={`fluxos-tab ${abaAtiva === ABAS.compartilhados ? "ativa" : ""}`}
            onClick={() => setAbaAtiva(ABAS.compartilhados)}
          >
            Compartilhados comigo
          </button>
        </div>

        <div className="fluxos-table-wrapper">
          {fluxosFiltrados.length > 0 && (
            <table className="fluxos-table">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Última execução</th>
                  <th>Proprietário</th>
                  <th aria-hidden="true"></th>
                </tr>
              </thead>
              <tbody>
                {fluxosFiltrados.map((fluxo) => (
                  <tr
                    key={fluxo.id}
                    className="fluxos-row-clickable"
                    onClick={() => abrirDetalhes(fluxo.id)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        abrirDetalhes(fluxo.id);
                      }
                    }}
                    tabIndex={0}
                  >
                    <td data-label="Nome">
                      <span className="fluxos-name-cell">
                        <span className="fluxos-name-icon" aria-hidden="true">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                          </svg>
                        </span>
                        {fluxo.nome}
                      </span>
                    </td>
                    <td data-label="Última execução">{fluxo.ultimaExecucao}</td>
                    <td data-label="Proprietário">
                      <span className="fluxos-owner-cell">
                        <span className="fluxos-owner-avatar">{iniciais(fluxo.proprietario)}</span>
                        {fluxo.proprietario}
                      </span>
                    </td>
                    <td className="fluxos-chevron-cell" aria-hidden="true">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                        <path d="m9 6 6 6-6 6" />
                      </svg>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {!carregando && fluxosFiltrados.length === 0 && (
            <div className="fluxos-empty-state">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="4" width="7" height="6" rx="1.5" />
                <rect x="14" y="4" width="7" height="6" rx="1.5" />
                <rect x="8.5" y="14" width="7" height="6" rx="1.5" />
              </svg>
              <p>{tituloAba}</p>
            </div>
          )}

          {carregando && <div className="fluxos-empty-state">Carregando fluxos...</div>}
        </div>
      </div>
    </section>
  );
}

export default Fluxos;
