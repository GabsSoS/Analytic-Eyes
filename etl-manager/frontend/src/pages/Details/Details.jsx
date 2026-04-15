import "./Details.css";
import { useCallback, useEffect, useMemo, useState } from "react";
import Editor from "@monaco-editor/react";
import { Link, useParams } from "react-router-dom";
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
};

const PERMISSOES_COLABORADOR = ["edit", "execute", "view"];

const normalizarDetalhes = (dadosDetalhes) => ({
  ...DETALHE_INICIAL,
  ...(dadosDetalhes ?? {}),
  collaborators: Array.isArray(dadosDetalhes?.collaborators)
    ? dadosDetalhes.collaborators
    : [],
});

const formatarDataHora = (valor) => {
  if (!valor) {
    return "Sem informacao";
  }

  const data = new Date(valor);

  if (Number.isNaN(data.getTime())) {
    return "Sem informacao";
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
    return "Nao iniciado";
  }

  const data = new Date(valor);

  if (Number.isNaN(data.getTime())) {
    return "Nao iniciado";
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
    return "Sem informacao";
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
    return { label: "Sucesso", classe: "success", resumo: "On" };
  }

  if (statusNormalizado === "RUNNING") {
    return { label: "Executando", classe: "running", resumo: "On" };
  }

  if (statusNormalizado === "FAILED") {
    return { label: "Falha", classe: "failed", resumo: "Falha" };
  }

  if (statusNormalizado === "PENDING") {
    return { label: "Pendente", classe: "pending", resumo: "Pendente" };
  }

  return { label: "Sem execucao", classe: "idle", resumo: "Sem execucao" };
};

function Details() {
  const { id } = useParams();
  const [detalhes, setDetalhes] = useState(DETALHE_INICIAL);
  const [historico, setHistorico] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");
  const [modalHistoricoAberto, setModalHistoricoAberto] = useState(false);
  const [modalEdicaoAberto, setModalEdicaoAberto] = useState(false);
  const [modalCodigoAberto, setModalCodigoAberto] = useState(false);
  const [usuariosDisponiveis, setUsuariosDisponiveis] = useState([]);
  const [carregandoUsuarios, setCarregandoUsuarios] = useState(false);
  const [carregandoCodigo, setCarregandoCodigo] = useState(false);
  const [iniciandoPipeline, setIniciandoPipeline] = useState(false);
  const [salvandoEdicao, setSalvandoEdicao] = useState(false);
  const [salvandoCodigo, setSalvandoCodigo] = useState(false);
  const [erroEdicao, setErroEdicao] = useState("");
  const [erroCodigo, setErroCodigo] = useState("");
  const [codigoPipe, setCodigoPipe] = useState("");
  const [formEdicao, setFormEdicao] = useState({
    name: "",
    description: "",
    owner: "",
    collaborators: [],
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
      console.error("Erro ao buscar detalhes da pipe:", error);
      setErro("Nao foi possivel carregar os detalhes da pipe.");
    } finally {
      setCarregando(false);
    }
  }, [id]);

  useEffect(() => {
    buscarDados();
  }, [buscarDados]);

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
    });
    setModalEdicaoAberto(true);

    if (usuariosDisponiveis.length > 0 || carregandoUsuarios) {
      return;
    }

    setCarregandoUsuarios(true);

    try {
      const response = await api.get("users/");
      const users = response.data?.users ?? [];
      setUsuariosDisponiveis(
        users
          .map((user) => user.username)
          .filter(Boolean)
          .sort((userA, userB) => userA.localeCompare(userB, "pt-BR"))
      );
    } catch (error) {
      console.error("Erro ao buscar usuarios para edicao:", error);
    } finally {
      setCarregandoUsuarios(false);
    }
  }, [carregandoUsuarios, detalhes, usuariosDisponiveis.length]);

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

  const salvarEdicao = async () => {
    const nome = formEdicao.name.trim();

    if (!nome) {
      setErroEdicao("Preencha o nome da pipe antes de salvar.");
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
        setErroEdicao("Nao repita o mesmo colaborador na lista.");
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
      console.error("Erro ao atualizar pipe:", error);
      setErroEdicao(
        error.response?.data?.error || "Nao foi possivel salvar as alteracoes."
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
        setErroCodigo("Nenhum codigo foi retornado para esta pipe.");
      }
    } catch (error) {
      console.error("Erro ao carregar codigo atual da pipe:", error);
      setErroCodigo("Nao foi possivel carregar o codigo atual da pipe.");
    } finally {
      setCarregandoCodigo(false);
    }
  };

  const salvarCodigo = async () => {
    if (!codigoPipe.trim()) {
      setErroCodigo("Adicione um codigo para salvar a pipe.");
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
      console.error("Erro ao atualizar codigo da pipe:", error);
      setErroCodigo(
        error.response?.data?.error || "Nao foi possivel salvar o codigo."
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
      console.error("Erro ao iniciar a pipe:", error);
      setErro(
        error.response?.data?.error || "Nao foi possivel iniciar a pipeline."
      );
    } finally {
      setIniciandoPipeline(false);
    }
  };

  return (
    <section className="details-page">
      <div className="details-shell">
        <header className="details-breadcrumb">
          <Link to="/fluxos">Fluxo</Link>
          <span className="details-breadcrumb-separator">{">"}</span>
          <strong>{detalhes.name || `Pipe ${id}`}</strong>
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
                      {iniciandoPipeline ? "Iniciando..." : "Start"}
                    </button>
                    <button
                      type="button"
                      className="details-link-button"
                      onClick={abrirModalCodigo}
                    >
                      Edit code
                    </button>
                    <button
                      type="button"
                      className="details-link-button"
                      onClick={abrirModalEdicao}
                    >
                      Edit
                    </button>
                  </div>
                </div>

                <div className="details-card-body">
                  <div className="details-meta-grid">
                    <div className="details-block">
                      <span className="details-label">Flow</span>
                      <strong className="details-value">{detalhes.name || "Sem nome"}</strong>
                    </div>

                    <div className="details-block compact">
                      <span className="details-label">Status</span>
                      <strong className={`details-status-summary ${statusAtual.classe}`}>
                        {statusAtual.resumo}
                      </strong>
                    </div>

                    <div className="details-block details-description">
                      <span className="details-label">Descricao</span>
                      <p>
                        {detalhes.description || "Sem descricao cadastrada para esta pipe."}
                      </p>
                    </div>

                    <div className="details-block compact">
                      <span className="details-label">Data de criacao</span>
                      <strong className="details-value muted">
                        {formatarDataHora(detalhes.created_at)}
                      </strong>
                    </div>
                  </div>

                  <div className="details-footer-meta">
                    <div className="details-block compact">
                      <span className="details-label">Usuario Primario</span>
                      <strong className="details-value muted">
                        User, {detalhes.owner || "Sem proprietario"}
                      </strong>
                    </div>

                    <div className="details-block compact">
                      <span className="details-label">ETL</span>
                      <strong className="details-value muted">
                        {detalhes.etl_name || "Nao informada"}
                      </strong>
                    </div>
                  </div>
                </div>
              </section>

              <section className="details-card">
                <div className="details-card-header">
                  <h2>Historico de execucao</h2>
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
                      aria-label="Atualizar historico"
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
                        <th>Iniciar</th>
                        <th>Duracao</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {historicoResumido.map((execucao) => (
                        <tr key={execucao.id}>
                          <td data-label="Iniciar">{execucao.inicio}</td>
                          <td data-label="Duracao">{execucao.duracao}</td>
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
                      Nenhuma execucao encontrada para esta pipe.
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
                        <small>{colaborador.permission}</small>
                      </div>
                    ))
                  ) : (
                    <div className="details-empty-side">
                      Nenhum colaborador compartilhado.
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
              <h2 id="details-modal-title">Historico completo de execucao</h2>
              <button
                type="button"
                className="details-modal-close"
                onClick={() => setModalHistoricoAberto(false)}
                aria-label="Fechar historico completo"
              >
                ×
              </button>
            </div>

            <div className="details-modal-body">
              <table className="details-history-table">
                <thead>
                  <tr>
                    <th>Iniciar</th>
                    <th>Duracao</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {historicoFormatado.map((execucao) => (
                    <tr key={`modal-${execucao.id}`}>
                      <td data-label="Iniciar">{execucao.inicio}</td>
                      <td data-label="Duracao">{execucao.duracao}</td>
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
              <h2 id="details-edit-modal-title">Editar informacoes da pipe</h2>
              <button
                type="button"
                className="details-modal-close"
                onClick={() => setModalEdicaoAberto(false)}
                aria-label="Fechar edicao da pipe"
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
                    placeholder="Digite o nome da pipeline"
                  />
                </label>

                <label className="details-edit-field">
                  <span>Descricao</span>
                  <textarea
                    value={formEdicao.description}
                    onChange={(event) =>
                      atualizarCampoEdicao("description", event.target.value)
                    }
                    placeholder="Descreva o objetivo da pipe"
                    rows={4}
                  />
                </label>

                <label className="details-edit-field">
                  <span>Usuario primario</span>
                  <select
                    value={formEdicao.owner}
                    onChange={(event) =>
                      atualizarCampoEdicao("owner", event.target.value)
                    }
                    disabled={carregandoUsuarios}
                  >
                    <option value="">
                      {carregandoUsuarios
                        ? "Carregando usuarios..."
                        : "Selecione um usuario"}
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
                                ? "Carregando usuarios..."
                                : "Selecione um usuario"}
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
                                {permissao}
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
                    {salvandoEdicao ? "Salvando..." : "Salvar alteracoes"}
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
              <h2 id="details-code-modal-title">Editar codigo da pipe</h2>
              <button
                type="button"
                className="details-modal-close"
                onClick={() => setModalCodigoAberto(false)}
                aria-label="Fechar edicao de codigo"
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
                    Carregando codigo da pipe...
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
                    {salvandoCodigo ? "Salvando..." : "Salvar codigo"}
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
