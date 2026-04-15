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

const normalizarFluxo = (fluxo, index) => ({
  id: fluxo.id ?? `${fluxo.nome ?? fluxo.name ?? "fluxo"}-${index}`,
  nome: fluxo.nome ?? fluxo.name ?? "Fluxo sem nome",
  ultimaExecucao:
    fluxo.ultimaExecucao ??
    fluxo.ultima_execucao ??
    fluxo.lastRun ??
    fluxo.last_run ??
    "Sem execucao",
  proprietario:
    fluxo.proprietario ??
    fluxo.owner ??
    fluxo.proprietary ??
    "Sem proprietario",
});

function Fluxos() {
  const navigate = useNavigate();
  const [abaAtiva, setAbaAtiva] = useState(ABAS.meus);
  const [fluxos, setFluxos] = useState(FLUXOS_MOCKADOS);
  const [usuarioAtual, setUsuarioAtual] = useState(
    localStorage.getItem("username") || "Lucas Souza"
  );
  const [carregando, setCarregando] = useState(false);

  useEffect(() => {
    const buscarFluxos = async () => {
      setCarregando(true);

      try {
        const response = await api.get("pipelines/");
        const payload = response.data;
        const listaRecebida = Array.isArray(payload)
          ? payload
          : payload?.results ?? payload?.pipelines ?? payload?.fluxos ?? [];

        if (Array.isArray(listaRecebida) && listaRecebida.length > 0) {
          setFluxos(listaRecebida.map(normalizarFluxo));
        }

        const usuarioDaApi =
          payload?.currentUser ??
          payload?.current_user ??
          payload?.user ??
          payload?.username;

        if (usuarioDaApi) {
          setUsuarioAtual(usuarioDaApi);
          localStorage.setItem("username", usuarioDaApi);
        }
      } catch (error) {
        console.error("Erro ao buscar fluxos:", error);
      } finally {
        setCarregando(false);
      }
    };

    buscarFluxos();
  }, []);

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
