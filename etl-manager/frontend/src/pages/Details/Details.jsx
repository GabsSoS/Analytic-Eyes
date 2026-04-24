import "./Details.css";
import { useCallback, useEffect, useMemo, useState } from "react";
import Editor from "@monaco-editor/react";
import { Link, useParams, useNavigate } from "react-router-dom";
import api from "../../services/api";

const DETALHE_INICIAL = {
  id: null,
  name: "",
  description: "",
  owner: "",
  etl_name: "",
  main_code: "",
  created_at: null,
  status: "NOT_RUN",
  collaborators: [],
  trigger_sources: [],
  trigger_targets: [],
};

const PERMISSOES_COLABORADOR = ["edit", "execute", "view"];
const PERMISSOES_LABELS = {
  edit: "Editar",
  execute: "Executar",
  view: "Visualizar",
};

const normalizarDetalhes = (dadosDetalhes) => ({
  ...DETALHE_INICIAL,
  ...(dadosDetalhes ?? {}),
  collaborators: Array.isArray(dadosDetalhes?.collaborators)
    ? dadosDetalhes.collaborators
    : [],
  trigger_sources: Array.isArray(dadosDetalhes?.trigger_sources)
    ? dadosDetalhes.trigger_sources
    : [],
  trigger_targets: Array.isArray(dadosDetalhes?.trigger_targets)
    ? dadosDetalhes.trigger_targets
    : [],
});

const formatarDataHora = (valor) => {
  if (!valor) {
    return "Sem informação";
  }

  const data = new Date(valor);

  if (Number.isNaN(data.getTime())) {
    return "Sem informação";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(data);
};

const formatarInicioExecucao = (valor) => {
  if (!valor) {
    return "Não iniciado";
  }

  const data = new Date(valor);

  if (Number.isNaN(data.getTime())) {
    return "Não iniciado";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(data);
};

const formatarDuracao = (inicio, fim) => {
  if (!inicio) {
    return "Aguardando";
  }

  const inicioData = new Date(inicio);
  const fimData = fim ? new Date(fim) : new Date();

  if (Number.isNaN(inicioData.getTime()) || Number.isNaN(fimData.getTime())) {
    return "Sem informação";
  }

  const diferencaMs = Math.max(fimData.getTime() - inicioData.getTime(), 0);

  if (diferencaMs < 1000) {
    return `${diferencaMs}ms`;
  }

  const totalSegundos = Math.floor(diferencaMs / 1000);
  const horas = Math.floor(totalSegundos / 3600);
  const minutos = Math.floor((totalSegundos % 3600) / 60);
  const segundos = totalSegundos % 60;

  return [horas, minutos, segundos]
    .map((valor) => String(valor).padStart(2, "0"))
    .join(":");
};

const obterStatusVisual = (status) => {
  const statusNormalizado = String(status ?? "").toUpperCase();

  if (statusNormalizado === "SUCCESS") {
    return { label: "Sucesso", classe: "success", resumo: "Sucesso" };
  }

  if (statusNormalizado === "RUNNING") {
    return { label: "Executando", classe: "running", resumo: "Executando" };
  }

  if (statusNormalizado === "FAILED") {
    return { label: "Falha", classe: "failed", resumo: "Falha" };
  }

  if (statusNormalizado === "PENDING") {
    return { label: "Pendente", classe: "pending", resumo: "Pendente" };
  }

  return { label: "Sem execução", classe: "idle", resumo: "Sem execução" };
};

function Details() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [detalhes, setDetalhes] = useState(DETALHE_INICIAL);
  const [historico, setHistorico] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");
  const [modalHistoricoAberto, setModalHistoricoAberto] = useState(false);
  const [modalEdicaoAberto, setModalEdicaoAberto] = useState(false);
  const [modalCodigoAberto, setModalCodigoAberto] = useState(false);
  const [modalDeleteAberto, setModalDeleteAberto] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [currentUser, setCurrentUser] = useState(null);
  const [usuariosDisponiveis, setUsuariosDisponiveis] = useState([]);
  const [pipelinesDisponiveis, setPipelinesDisponiveis] = useState([]);
  const [carregandoUsuarios, setCarregandoUsuarios] = useState(false);
  const [carregandoPipelines, setCarregandoPipelines] = useState(false);
  const [carregandoCodigo, setCarregandoCodigo] = useState(false);
  const [iniciandoPipeline, setIniciandoPipeline] = useState(false);
  const [salvandoEdicao, setSalvandoEdicao] = useState(false);
  const [salvandoCodigo, setSalvandoCodigo] = useState(false);
  const [erroEdicao, setErroEdicao] = useState("");
  const [erroCodigo, setErroCodigo] = useState("");
  const [codigoPipe, setCodigoPipe] = useState("");
  const [novoAnchorId, setNovoAnchorId] = useState("");
  const [formEdicao, setFormEdicao] = useState({
    name: "",
    description: "",
    owner: "",
    collaborators: [],
    trigger_source_ids: [],
  });

  const buscarDados = useCallback(async () => {
    setCarregando(true);
    setErro("");

    try {
      const [detalhesResponse, historicoResponse] = await Promise.all([
        api.get(`pipelines/${id}/details/`),
        api.get(`pipelines/${id}/runs/`),
      ]);

      const dadosDetalhes = detalhesResponse.data ?? DETALHE_INICIAL;
      const dadosHistorico = historicoResponse.data;
      const listaRuns = Array.isArray(dadosHistorico)
        ? dadosHistorico
        : dadosHistorico?.runs ??
          dadosHistorico?.[`Pipeline ${id}`] ??
          [];

      setDetalhes(normalizarDetalhes(dadosDetalhes));
      setHistorico(Array.isArray(listaRuns) ? listaRuns : []);
    } catch (error) {
      console.error("Erro ao buscar detalhes do fluxo:", error);
      setErro("Não foi possível carregar os detalhes do fluxo.");
    } finally {
      setCarregando(false);
    }
  }, [id]);

  useEffect(() => {
    buscarDados();
  }, [buscarDados]);

  useEffect(() => {
    let mounted = true;
    async function loadUser() {
      try {
        const res = await api.get("auth/me/");
        if (!mounted) return;
        setCurrentUser(res.data?.username ?? null);
      } catch (err) {
        // não fatal — apenas não mostrar botão de delete
      }
    }

    loadUser();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (!modalCodigoAberto) {
      setCodigoPipe(String(detalhes.main_code ?? ""));
    }
  }, [detalhes.main_code, modalCodigoAberto]);

  const statusAtual = useMemo(
    () => obterStatusVisual(detalhes.status),
    [detalhes.status]
  );

  const historicoFormatado = useMemo(
    () =>
      [...historico]
        .sort((execucaoA, execucaoB) => {
          const dataA =
            new Date(
              execucaoA.started_at ?? execucaoA.finished_at ?? execucaoA.created_at ?? 0
            ).getTime() || 0;
          const dataB =
            new Date(
              execucaoB.started_at ?? execucaoB.finished_at ?? execucaoB.created_at ?? 0
            ).getTime() || 0;

          return dataB - dataA;
        })
        .map((execucao) => ({
          id: execucao.id,
          inicio: formatarInicioExecucao(execucao.started_at),
          duracao: formatarDuracao(execucao.started_at, execucao.finished_at),
          status: obterStatusVisual(execucao.status),
        })),
    [historico]
  );

  const historicoResumido = useMemo(
    () => historicoFormatado.slice(0, 5),
    [historicoFormatado]
  );

  const pipelinesAncoradasSelecionadas = useMemo(
    () =>
      pipelinesDisponiveis.filter((pipeline) =>
        formEdicao.trigger_source_ids.includes(pipeline.id)
      ),
    [formEdicao.trigger_source_ids, pipelinesDisponiveis]
  );

  const opcoesAncoragem = useMemo(
    () =>
      pipelinesDisponiveis.filter((pipeline) => {
        if (pipeline.id === Number(id)) {
          return false;
        }

        return !formEdicao.trigger_source_ids.includes(pipeline.id);
      }),
    [formEdicao.trigger_source_ids, id, pipelinesDisponiveis]
  );

  const abrirModalEdicao = useCallback(async () => {
    setErroEdicao("");
    setFormEdicao({
      name: detalhes.name ?? "",
      description: detalhes.description ?? "",
      owner: detalhes.owner ?? "",
      collaborators: Array.isArray(detalhes.collaborators)
        ? detalhes.collaborators.map((colaborador) => ({
            username: colaborador.username ?? "",
            permission: colaborador.permission ?? "view",
          }))
        : [],
      trigger_source_ids: Array.isArray(detalhes.trigger_sources)
        ? detalhes.trigger_sources
            .map((pipeline) => Number(pipeline.id))
            .filter((pipelineId) => Number.isFinite(pipelineId))
        : [],
    });
    setNovoAnchorId("");
    setModalEdicaoAberto(true);

    if (
      (usuariosDisponiveis.length > 0 && pipelinesDisponiveis.length > 0) ||
      carregandoUsuarios ||
      carregandoPipelines
    ) {
      return;
    }

    setCarregandoUsuarios(true);
    setCarregandoPipelines(true);

    try {
      const [usersResponse, pipelinesResponse] = await Promise.all([
        api.get("users/"),
        api.get("pipelines/"),
      ]);
      const users = usersResponse.data?.users ?? [];
      const pipelines = pipelinesResponse.data?.pipelines ?? [];
      setUsuariosDisponiveis(
        users
          .map((user) => user.username)
          .filter(Boolean)
          .sort((userA, userB) => userA.localeCompare(userB, "pt-BR"))
      );
      setPipelinesDisponiveis(
        pipelines
          .map((pipeline) => ({
            id: Number(pipeline.id),
            name: pipeline.name ?? `Fluxo ${pipeline.id}`,
          }))
          .filter((pipeline) => Number.isFinite(pipeline.id))
          .sort((pipelineA, pipelineB) =>
            pipelineA.name.localeCompare(pipelineB.name, "pt-BR")
          )
      );
    } catch (error) {
      console.error("Erro ao buscar dados para edicao:", error);
    } finally {
      setCarregandoUsuarios(false);
      setCarregandoPipelines(false);
    }
  }, [
    carregandoPipelines,
    carregandoUsuarios,
    detalhes,
    pipelinesDisponiveis.length,
    usuariosDisponiveis.length,
  ]);

  const atualizarCampoEdicao = (campo, valor) => {
    setFormEdicao((atual) => ({
      ...atual,
      [campo]: valor,
    }));
  };

  const atualizarColaborador = (index, campo, valor) => {
    setFormEdicao((atual) => ({
      ...atual,
      collaborators: atual.collaborators.map((colaborador, collaboratorIndex) =>
        collaboratorIndex === index
          ? { ...colaborador, [campo]: valor }
          : colaborador
      ),
    }));
  };

  const adicionarColaborador = () => {
    setFormEdicao((atual) => ({
      ...atual,
      collaborators: [
        ...atual.collaborators,
        { username: "", permission: "view" },
      ],
    }));
  };

  const removerColaborador = (index) => {
    setFormEdicao((atual) => ({
      ...atual,
      collaborators: atual.collaborators.filter(
        (_, collaboratorIndex) => collaboratorIndex !== index
      ),
    }));
  };

  const adicionarAncoragem = () => {
    const pipelineId = Number(novoAnchorId);

    if (!pipelineId) {
      return;
    }

    setFormEdicao((atual) => {
      if (atual.trigger_source_ids.includes(pipelineId)) {
        return atual;
      }

      return {
        ...atual,
        trigger_source_ids: [...atual.trigger_source_ids, pipelineId],
      };
    });
    setNovoAnchorId("");
  };

  const removerAncoragem = (pipelineId) => {
    setFormEdicao((atual) => ({
      ...atual,
      trigger_source_ids: atual.trigger_source_ids.filter((idAtual) => idAtual !== pipelineId),
    }));
  };

  const salvarEdicao = async () => {
    const nome = formEdicao.name.trim();

    if (!nome) {
      setErroEdicao("Preencha o nome do fluxo antes de salvar.");
      return;
    }

    const collaborators = formEdicao.collaborators
      .map((colaborador) => ({
        username: String(colaborador.username ?? "").trim(),
        permission: String(colaborador.permission ?? "view").trim(),
      }))
      .filter((colaborador) => colaborador.username);

    const usernamesUnicos = new Set();
    for (const collaborator of collaborators) {
      if (usernamesUnicos.has(collaborator.username)) {
        setErroEdicao("Não repita o mesmo colaborador na lista.");
        return;
      }

      usernamesUnicos.add(collaborator.username);
    }

    setSalvandoEdicao(true);
    setErroEdicao("");

    try {
      const payload = {
        name: nome,
        description: formEdicao.description.trim(),
        anchor_pipeline_ids: formEdicao.trigger_source_ids,
      };

      if (formEdicao.owner.trim() && formEdicao.owner.trim() !== detalhes.owner) {
        payload.owner = formEdicao.owner.trim();
      }

      const colaboradoresAtuais = JSON.stringify(
        (detalhes.collaborators ?? [])
          .map((colaborador) => ({
            username: String(colaborador.username ?? "").trim(),
            permission: String(colaborador.permission ?? "view").trim(),
          }))
          .sort((colaboradorA, colaboradorB) =>
            colaboradorA.username.localeCompare(colaboradorB.username, "pt-BR")
          )
      );

      const colaboradoresEditados = JSON.stringify(
        [...collaborators].sort((colaboradorA, colaboradorB) =>
          colaboradorA.username.localeCompare(colaboradorB.username, "pt-BR")
        )
      );

      if (colaboradoresEditados !== colaboradoresAtuais) {
        payload.collaborators = collaborators;
      }

      const response = await api.put(`pipelines/${id}/update/`, payload);

      setDetalhes(normalizarDetalhes(response.data));
      setModalEdicaoAberto(false);
    } catch (error) {
      console.error("Erro ao atualizar fluxo:", error);
      setErroEdicao(
        error.response?.data?.error || "Não foi possível salvar as alterações."
      );
    } finally {
      setSalvandoEdicao(false);
    }
  };

  const abrirModalCodigo = async () => {
    setErroCodigo("");
    setCodigoPipe(String(detalhes.main_code ?? ""));
    setModalCodigoAberto(true);
    setCarregandoCodigo(true);

    try {
      const response = await api.get(`pipelines/${id}/details/`);
      const dadosDetalhes = response.data ?? {};
      const codigoAtual = String(dadosDetalhes.main_code ?? "");

      setDetalhes((atual) => ({
        ...atual,
        ...normalizarDetalhes(dadosDetalhes),
      }));
      setCodigoPipe(codigoAtual);

      if (!codigoAtual.trim()) {
        setErroCodigo("Nenhum código foi retornado para este fluxo.");
      }
    } catch (error) {
      console.error("Erro ao carregar código atual do fluxo:", error);
      setErroCodigo("Não foi possível carregar o código atual do fluxo.");
    } finally {
      setCarregandoCodigo(false);
    }
  };

  const salvarCodigo = async () => {
    if (!codigoPipe.trim()) {
      setErroCodigo("Adicione um código para salvar o fluxo.");
      return;
    }

    setSalvandoCodigo(true);
    setErroCodigo("");

    try {
      const response = await api.put(`pipelines/${id}/update/`, {
        main_code: codigoPipe,
      });

      setDetalhes(normalizarDetalhes(response.data));
      setModalCodigoAberto(false);
    } catch (error) {
      console.error("Erro ao atualizar código do fluxo:", error);
      setErroCodigo(
        error.response?.data?.error || "Não foi possível salvar o código."
      );
    } finally {
      setSalvandoCodigo(false);
    }
  };

  const iniciarPipeline = async () => {
    setIniciandoPipeline(true);
    setErro("");

    try {
      await api.post(`pipelines/${id}/`);
      await buscarDados();
    } catch (error) {
      console.error("Erro ao iniciar o fluxo:", error);
      setErro(
        error.response?.data?.error || "Não foi possível iniciar o fluxo."
      );
    } finally {
      setIniciandoPipeline(false);
    }
  };

  const confirmarDelete = () => {
    if (!detalhes?.name) return false;
    return String(deleteConfirmText ?? "").trim() === String(detalhes.name ?? "");
  };

  const deletarPipeline = async () => {
    if (!confirmarDelete()) {
      setDeleteError("Digite o nome exato do fluxo para confirmar a exclusão.");
      return;
    }

    setDeleting(true);
    setDeleteError("");

    try {
      await api.post(`pipelines/${id}/delete/`, { confirm_name: detalhes.name });
      navigate("/fluxos");
    } catch (error) {
      console.error("Erro ao excluir o fluxo:", error);
      setDeleteError(error.response?.data?.error || 'Não foi possível excluir o fluxo.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <section className="details-page">
      <div className="details-shell">
        <header className="details-breadcrumb">
           <Link to="/fluxos">Fluxos</Link>
          <span className="details-breadcrumb-separator">{">"}</span>
           <strong>{detalhes.name || `Fluxo ${id}`}</strong>
        </header>

        {erro && <div className="details-feedback error">{erro}</div>}

        {carregando ? (
          <div className="details-feedback">Carregando detalhes...</div>
        ) : (
          <div className="details-grid">
            <div className="details-main-column">
              <section className="details-card">
                <div className="details-card-header">
                  <h1>Detalhes</h1>
                  <div className="details-card-actions">
                    <button
                      type="button"
                      className="details-start-button"
                      onClick={iniciarPipeline}
                      disabled={iniciandoPipeline}
                    >
                       {iniciandoPipeline ? "Iniciando..." : "Iniciar"}
                    </button>
                    <button
                      type="button"
                      className="details-link-button"
                      onClick={abrirModalCodigo}
                    >
                       Editar código
                    </button>
                    <button
                      type="button"
                      className="details-link-button"
                      onClick={abrirModalEdicao}
                    >
                       Editar
                    </button>
                                {currentUser && detalhes.owner === currentUser && (
                                  <button
                                    type="button"
                                    className="details-delete-button"
                                    onClick={() => { setDeleteError(""); setDeleteConfirmText(""); setModalDeleteAberto(true); }}
                                  >
                                    Excluir
                                  </button>
                                )}
                  </div>
                </div>

                <div className="details-card-body">
                  <div className="details-meta-grid">
                    <div className="details-block">
                      <span className="details-label">Fluxo</span>
                      <strong className="details-value">{detalhes.name || "Sem nome"}</strong>
                    </div>

                    <div className="details-block compact">
                      <span className="details-label">Status</span>
                      <strong className={`details-status-summary ${statusAtual.classe}`}>
                        {statusAtual.resumo}
                      </strong>
                    </div>

                    <div className="details-block details-description">
                      <span className="details-label">Descrição</span>
                      <p>
                        {detalhes.description || "Sem descrição cadastrada para este fluxo."}
                      </p>
                    </div>

                    <div className="details-block compact">
                      <span className="details-label">Data de criação</span>
                      <strong className="details-value muted">
                        {formatarDataHora(detalhes.created_at)}
                      </strong>
                    </div>
                  </div>

                  <div className="details-footer-meta">
                    <div className="details-block compact">
                      <span className="details-label">Usuário primário</span>
                      <strong className="details-value muted">
                        {detalhes.owner || "Sem proprietário"}
                      </strong>
                    </div>

                    <div className="details-block compact">
                      <span className="details-label">ETL</span>
                      <strong className="details-value muted">
                        {detalhes.etl_name || "Não informada"}
                      </strong>
                    </div>
                  </div>
                </div>
              </section>

              <section className="details-card">
                <div className="details-card-header">
                  <h2>Histórico de execução</h2>
                  <div className="details-card-actions">
                    {historicoFormatado.length > 5 && (
                      <button
                        type="button"
                        className="details-link-button"
                        onClick={() => setModalHistoricoAberto(true)}
                      >
                        Mostrar mais
                      </button>
                    )}
                    <button
                      type="button"
                      className="details-refresh-button"
                      onClick={buscarDados}
                      aria-label="Atualizar histórico"
                    >
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M20 12a8 8 0 1 1-2.34-5.66" />
                        <path d="M20 4v6h-6" />
                      </svg>
                    </button>
                  </div>
                </div>

                <div className="details-history-table-wrapper">
                  <table className="details-history-table">
                    <thead>
                        <tr>
                          <th>Início</th>
                          <th>Duração</th>
                          <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                      {historicoResumido.map((execucao) => (
                        <tr key={execucao.id}>
                          <td data-label="Início">{execucao.inicio}</td>
                          <td data-label="Duração">{execucao.duracao}</td>
                          <td
                            data-label="Status"
                            className={`details-history-status ${execucao.status.classe}`}
                          >
                            {execucao.status.label}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {historicoResumido.length === 0 && (
                    <div className="details-empty-state">
                      Nenhuma execução encontrada para este fluxo.
                    </div>
                  )}
                </div>
              </section>
            </div>

            <aside className="details-side-column">
              <section className="details-card">
                <div className="details-card-header">
                  <h2>Colaboradores</h2>
                </div>

                <div className="details-collaborators-list">
                  {detalhes.collaborators.length > 0 ? (
                    detalhes.collaborators.map((colaborador) => (
                      <div key={colaborador.id} className="details-collaborator-item">
                        <span>{colaborador.username}</span>
                        <small>{PERMISSOES_LABELS[colaborador.permission] || colaborador.permission}</small>
                      </div>
                    ))
                  ) : (
                    <div className="details-empty-side">
                      Nenhum colaborador compartilhado.
                    </div>
                  )}
                </div>
              </section>

              <section className="details-card">
                <div className="details-card-header">
                  <h2>Ancoragens</h2>
                </div>

                <div className="details-anchor-section">
                  <span className="details-label">Executa apos sucesso de</span>
                  {detalhes.trigger_sources.length > 0 ? (
                    <div className="details-anchor-list">
                      {detalhes.trigger_sources.map((pipeline) => (
                        <div key={`source-${pipeline.id}`} className="details-anchor-item">
                          {pipeline.name}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="details-empty-side">
                      Nenhuma ancoragem configurada.
                    </div>
                  )}
                </div>

                <div className="details-anchor-section">
                  <span className="details-label">Dispara automaticamente</span>
                  {detalhes.trigger_targets.length > 0 ? (
                    <div className="details-anchor-list">
                      {detalhes.trigger_targets.map((pipeline) => (
                        <div key={`target-${pipeline.id}`} className="details-anchor-item">
                          {pipeline.name}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="details-empty-side">
                      Nenhum fluxo depende deste.
                    </div>
                  )}
                </div>
              </section>
            </aside>
          </div>
        )}
      </div>

      {modalHistoricoAberto && (
        <div
          className="details-modal-overlay"
          onClick={() => setModalHistoricoAberto(false)}
          role="presentation"
        >
          <div
            className="details-modal"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="details-modal-title"
          >
            <div className="details-card-header">
              <h2 id="details-modal-title">Histórico completo de execução</h2>
              <button
                type="button"
                className="details-modal-close"
                onClick={() => setModalHistoricoAberto(false)}
                aria-label="Fechar histórico completo"
              >
                ×
              </button>
            </div>

            <div className="details-modal-body">
              <table className="details-history-table">
                <thead>
                  <tr>
                    <th>Início</th>
                    <th>Duração</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {historicoFormatado.map((execucao) => (
                      <tr key={`modal-${execucao.id}`}>
                      <td data-label="Início">{execucao.inicio}</td>
                      <td data-label="Duração">{execucao.duracao}</td>
                      <td
                        data-label="Status"
                        className={`details-history-status ${execucao.status.classe}`}
                      >
                        {execucao.status.label}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {modalEdicaoAberto && (
        <div
          className="details-modal-overlay"
          onClick={() => setModalEdicaoAberto(false)}
          role="presentation"
        >
          <div
            className="details-modal details-edit-modal"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="details-edit-modal-title"
          >
            <div className="details-card-header">
              <h2 id="details-edit-modal-title">Editar informações do fluxo</h2>
              <button
                type="button"
                className="details-modal-close"
                onClick={() => setModalEdicaoAberto(false)}
                aria-label="Fechar edição do fluxo"
              >
                ×
              </button>
            </div>

            <div className="details-modal-body">
              <div className="details-edit-form">
                {erroEdicao && (
                  <div className="details-feedback error details-edit-feedback">
                    {erroEdicao}
                  </div>
                )}

                <label className="details-edit-field">
                  <span>Nome do fluxo</span>
                  <input
                    type="text"
                    value={formEdicao.name}
                    onChange={(event) =>
                      atualizarCampoEdicao("name", event.target.value)
                    }
                    placeholder="Digite o nome do fluxo"
                  />
                </label>

                <label className="details-edit-field">
                  <span>Descrição</span>
                  <textarea
                    value={formEdicao.description}
                    onChange={(event) =>
                      atualizarCampoEdicao("description", event.target.value)
                    }
                    placeholder="Descreva o objetivo do fluxo"
                    rows={4}
                  />
                </label>

                <label className="details-edit-field">
                  <span>Usuário primário</span>
                  <select
                    value={formEdicao.owner}
                    onChange={(event) =>
                      atualizarCampoEdicao("owner", event.target.value)
                    }
                    disabled={carregandoUsuarios}
                  >
                    <option value="">
                      {carregandoUsuarios
                        ? "Carregando usuários..."
                        : "Selecione um usuário"}
                    </option>
                    {usuariosDisponiveis.map((usuario) => (
                      <option key={usuario} value={usuario}>
                        {usuario}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="details-edit-collaborators">
                  <div className="details-edit-collaborators-header">
                    <span>Executar apos sucesso de</span>
                  </div>

                  <div className="details-anchor-picker">
                    <select
                      value={novoAnchorId}
                      onChange={(event) => setNovoAnchorId(event.target.value)}
                      disabled={carregandoPipelines}
                    >
                      <option value="">
                        {carregandoPipelines
                          ? "Carregando pipelines..."
                          : "Selecione uma pipeline"}
                      </option>
                      {opcoesAncoragem.map((pipeline) => (
                        <option key={pipeline.id} value={pipeline.id}>
                          {pipeline.name}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      className="details-link-button"
                      onClick={adicionarAncoragem}
                      disabled={!novoAnchorId}
                    >
                      Adicionar
                    </button>
                  </div>

                  {pipelinesAncoradasSelecionadas.length > 0 ? (
                    <div className="details-anchor-list editable">
                      {pipelinesAncoradasSelecionadas.map((pipeline) => (
                        <div
                          key={`selected-anchor-${pipeline.id}`}
                          className="details-anchor-item editable"
                        >
                          <span>{pipeline.name}</span>
                          <button
                            type="button"
                            className="details-edit-remove"
                            onClick={() => removerAncoragem(pipeline.id)}
                          >
                            Remover
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="details-empty-state details-edit-empty">
                      Este fluxo nao possui ancoragens configuradas.
                    </div>
                  )}
                </div>

                <div className="details-edit-collaborators">
                  <div className="details-edit-collaborators-header">
                    <span>Colaboradores</span>
                    <button
                      type="button"
                      className="details-link-button"
                      onClick={adicionarColaborador}
                    >
                      Adicionar
                    </button>
                  </div>

                  {formEdicao.collaborators.length > 0 ? (
                    <div className="details-edit-collaborators-list">
                      {formEdicao.collaborators.map((colaborador, index) => (
                        <div
                          key={`${colaborador.username || "novo"}-${index}`}
                          className="details-edit-collaborator-row"
                        >
                          <select
                            value={colaborador.username}
                            onChange={(event) =>
                              atualizarColaborador(
                                index,
                                "username",
                                event.target.value
                              )
                            }
                            disabled={carregandoUsuarios}
                          >
                            <option value="">
                              {carregandoUsuarios
                                ? "Carregando usuários..."
                                : "Selecione um usuário"}
                            </option>
                            {usuariosDisponiveis.map((usuario) => (
                              <option key={usuario} value={usuario}>
                                {usuario}
                              </option>
                            ))}
                          </select>

                          <select
                            value={colaborador.permission}
                            onChange={(event) =>
                              atualizarColaborador(
                                index,
                                "permission",
                                event.target.value
                              )
                            }
                          >
                            {PERMISSOES_COLABORADOR.map((permissao) => (
                              <option key={permissao} value={permissao}>
                                {PERMISSOES_LABELS[permissao] || permissao}
                              </option>
                            ))}
                          </select>

                          <button
                            type="button"
                            className="details-edit-remove"
                            onClick={() => removerColaborador(index)}
                          >
                            Remover
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="details-empty-state details-edit-empty">
                      Nenhum colaborador configurado.
                    </div>
                  )}
                </div>

                <div className="details-edit-actions">
                  <button
                    type="button"
                    className="details-edit-secondary"
                    onClick={() => setModalEdicaoAberto(false)}
                    disabled={salvandoEdicao}
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    className="details-edit-primary"
                    onClick={salvarEdicao}
                    disabled={salvandoEdicao}
                  >
                    {salvandoEdicao ? "Salvando..." : "Salvar alterações"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {modalCodigoAberto && (
        <div
          className="details-modal-overlay"
          onClick={() => setModalCodigoAberto(false)}
          role="presentation"
        >
          <div
            className="details-modal details-code-modal"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="details-code-modal-title"  
          >
            <div className="details-card-header">
              <h2 id="details-code-modal-title">Editar código do fluxo</h2>
              <button
                type="button"
                className="details-modal-close"
                onClick={() => setModalCodigoAberto(false)}
                aria-label="Fechar edição de código"
              >
                ×
              </button>
            </div>

            <div className="details-modal-body details-code-modal-body">
              <div className="details-edit-form">
                {erroCodigo && (
                  <div className="details-feedback error details-edit-feedback">
                    {erroCodigo}
                  </div>
                )}

                {carregandoCodigo ? (
                  <div className="details-feedback details-code-loading">
                    Carregando código do fluxo...
                  </div>
                ) : (
                  <div className="details-code-editor">
                    <Editor
                      key={`pipe-code-${id}-${modalCodigoAberto ? "open" : "closed"}`}
                      height="52vh"
                      defaultLanguage="python"
                      language="python"
                      value={codigoPipe}
                      onChange={(value) => setCodigoPipe(value ?? "")}
                      options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                      }}
                    />
                  </div>
                )}

                <div className="details-edit-actions">
                  <button
                    type="button"
                    className="details-edit-secondary"
                    onClick={() => setModalCodigoAberto(false)}
                    disabled={salvandoCodigo || carregandoCodigo}
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    className="details-edit-primary"
                    onClick={salvarCodigo}
                    disabled={salvandoCodigo || carregandoCodigo}
                  >
                    {salvandoCodigo ? "Salvando..." : "Salvar código"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      {modalDeleteAberto && (
        <div
          className="details-modal-overlay"
          onClick={() => setModalDeleteAberto(false)}
          role="presentation"
        >
          <div
            className="details-modal details-edit-modal"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="details-delete-modal-title"
          >
            <div className="details-card-header">
              <h2 id="details-delete-modal-title">Excluir fluxo</h2>
              <button
                type="button"
                className="details-modal-close"
                onClick={() => setModalDeleteAberto(false)}
                aria-label="Fechar modal de exclusão"
              >
                ×
              </button>
            </div>

            <div className="details-modal-body">
              <div className="details-edit-form">
                <p>
                  Esta ação irá <strong>excluir permanentemente</strong> o fluxo.
                  Para confirmar, digite o nome do fluxo abaixo e clique em
                  <strong> Confirmar exclusão</strong>.
                </p>

                {deleteError && (
                  <div className="details-feedback error details-edit-feedback">
                    {deleteError}
                  </div>
                )}

                <label className="details-edit-field">
                  <span>Nome do fluxo</span>
                  <input
                    type="text"
                    value={deleteConfirmText}
                    onChange={(e) => setDeleteConfirmText(e.target.value)}
                    placeholder={`Digite: ${detalhes.name || "nome-do-fluxo"}`}
                  />
                </label>

                <div className="details-edit-actions">
                  <button
                    type="button"
                    className="details-edit-secondary"
                    onClick={() => setModalDeleteAberto(false)}
                    disabled={deleting}
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    className="details-delete-primary"
                    onClick={deletarPipeline}
                    disabled={deleting}
                  >
                    {deleting ? "Excluindo..." : "Confirmar exclusão"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default Details;
