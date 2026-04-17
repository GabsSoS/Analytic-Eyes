import "./Listagem.css";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";

const FLUXOS_MOCKADOS = [
  { id: 1, nome: "OP - Abertura do dia", ultimaExecucao: "Ha 1 hora", proprietario: "Lucas Souza" },
  { id: 2, nome: "Limpeza de tabela", ultimaExecucao: "4 semanas", proprietario: "Lucas Souza" },
  { id: 3, nome: "Limpeza planilhas ETL", ultimaExecucao: "2 dias", proprietario: "Lucas Souza" },
  { id: 4, nome: "Softwares sem licenca ETL", ultimaExecucao: "Ha 10 minutos", proprietario: "Lucas Souza" },
  { id: 5, nome: "Carga clientes ativos ETL", ultimaExecucao: "1 mes", proprietario: "Lucas Souza" },
  { id: 6, nome: "Normalizacao enderecos ETL", ultimaExecucao: "Ha 5 horas", proprietario: "Lucas Souza" },
  { id: 7, nome: "Inventario servidores ETL", ultimaExecucao: "Ha 1 ano", proprietario: "Lucas Souza" },
  { id: 8, nome: "Atualizacao precos ETL", ultimaExecucao: "15 minutos", proprietario: "Ana Lima" },
  { id: 9, nome: "Consolidacao financeira ETL", ultimaExecucao: "Ha 5 dias", proprietario: "Camila Rocha" },
  { id: 10, nome: "Monitoramento acessos ETL", ultimaExecucao: "Ha 3 horas", proprietario: "Pedro Martins" },
  { id: 11, nome: "Validacao contratos ETL", ultimaExecucao: "Ha 12 horas", proprietario: "Juliana Costa" },
  { id: 12, nome: "Integracao RH ETL", ultimaExecucao: "Ha 1 hora", proprietario: "Bruno Alves" },
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
      ? "Nenhum fluxo criado por voce."
      : "Nenhum fluxo compartilhado com voce.";

  return (
    <section className="fluxos-page">
      <div className="fluxos-shell">
        <header className="fluxos-header">
          <h1>Fluxo</h1>
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
            Compartilhado comigo
          </button>
        </div>

        <div className="fluxos-table-wrapper">
          <table className="fluxos-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Ultima execucao</th>
                <th>Proprietario</th>
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
                  <td data-label="Nome">{fluxo.nome}</td>
                  <td data-label="Ultima execucao">{fluxo.ultimaExecucao}</td>
                  <td data-label="Proprietario">{fluxo.proprietario}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {!carregando && fluxosFiltrados.length === 0 && (
            <div className="fluxos-empty-state">{tituloAba}</div>
          )}

          {carregando && <div className="fluxos-empty-state">Carregando fluxos...</div>}
        </div>
      </div>
    </section>
  );
}

export default Fluxos;
