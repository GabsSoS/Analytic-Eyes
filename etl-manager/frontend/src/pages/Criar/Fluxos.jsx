import "./Fluxos.css";
import { useEffect, useRef, useState } from "react";
import Editor from "@monaco-editor/react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../services/api";

function Criar() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditMode = Boolean(id);
  const nextLibraryId = useRef(1);
  const libraryInputRefs = useRef({});
  const [coOwners, setCoOwners] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [editorContent, setEditorContent] = useState("");
  const [editorLanguage, setEditorLanguage] = useState("python");
  const [jobName, setJobName] = useState("");
  const [description, setDescription] = useState("");
  const [libraries, setLibraries] = useState([
    { id: 0, value: "", locked: false },
  ]);
  const [pendingFocusId, setPendingFocusId] = useState(0);
  const [ownersList, setOwnersList] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingPipeline, setIsLoadingPipeline] = useState(false);
  const [configFile, setConfigFile] = useState(null);
  const [submitModal, setSubmitModal] = useState({
    status: "idle",
    message: "",
    pipelineId: null,
  });

  const addCoOwner = () => {
    const trimmedValue = inputValue.trim();

    if (trimmedValue && !coOwners.includes(trimmedValue)) {
      setCoOwners([...coOwners, trimmedValue]);
      setInputValue("");
    }
  };

  const removeCoOwner = (owner) => {
    setCoOwners(coOwners.filter((item) => item !== owner));
  };

  const handleKeyPress = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addCoOwner();
    }
  };

  const handleFiles = (files) => {
    const pyFiles = Array.from(files || []).filter((file) =>
      file.name.toLowerCase().endsWith(".py")
    );

    const renamedFiles = pyFiles.map(
      (file) =>
        new File([file], "main.py", {
          type: file.type || "text/x-python",
          lastModified: file.lastModified,
        })
    );

    setSelectedFiles(renamedFiles);

    if (renamedFiles.length > 0) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setEditorContent(event.target.result || "");
        setEditorLanguage("python");
      };
      reader.readAsText(renamedFiles[0]);
    }
  };

  const handleConfigFile = (files) => {
    const configFiles = Array.from(files || []).filter((file) =>
      file.name.toLowerCase().endsWith(".env") || file.name.toLowerCase().endsWith(".ini")
    );

    if (configFiles.length > 0) {
      setConfigFile(configFiles[0]);
    }
  };

  const syncEditorToSelectedFile = (value) => {
    const nextContent = value ?? "";

    setEditorContent(nextContent);
    setSelectedFiles((currentFiles) => {
      if (currentFiles.length === 0) {
        return [
          new File([nextContent], "main.py", {
            type: "text/x-python",
          }),
        ];
      }

      return currentFiles.map((file, index) =>
        index === 0
          ? new File([nextContent], "main.py", {
              type: file.type || "text/x-python",
              lastModified: Date.now(),
            })
          : file
      );
    });
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragActive(false);
    handleFiles(event.dataTransfer.files);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    setDragActive(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    if (event.target === event.currentTarget) {
      setDragActive(false);
    }
  };

  const updateLibrary = (libraryIndex, value) => {
    setLibraries((currentLibraries) =>
      currentLibraries.map((library, index) =>
        index === libraryIndex ? { ...library, value } : library
      )
    );
  };

  const lockLibrary = (libraryIndex) => {
    setLibraries((currentLibraries) => {
      const updatedLibraries = currentLibraries.map((library, index) =>
        index === libraryIndex ? { ...library, locked: true } : library
      );

      const hasEditableField = updatedLibraries.some((library) => !library.locked);

      if (hasEditableField) {
        return updatedLibraries;
      }

      const newLibraryId = nextLibraryId.current++;
      setPendingFocusId(newLibraryId);

      return [
        ...updatedLibraries,
        { id: newLibraryId, value: "", locked: false },
      ];
    });
  };

  const removeLibrary = (libraryIndex) => {
    setLibraries((currentLibraries) => {
      if (currentLibraries.length === 1) {
        return [{ id: currentLibraries[0].id, value: "", locked: false }];
      }

      return currentLibraries.filter((_, index) => index !== libraryIndex);
    });
  };

  const handleLibraryKeyDown = (event, libraryIndex) => {
    if (event.key === "Enter") {
      event.preventDefault();

      if (libraries[libraryIndex].value.trim()) {
        lockLibrary(libraryIndex);
      }
    }
  };

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const usersResponse = await api.get("users/");
        const users = usersResponse.data?.users ?? [];

        setOwnersList(users.map((user) => user.username));
      } catch (error) {
        console.error("Erro ao buscar usuarios:", error);
        setOwnersList([]);
      }
    };

    fetchUsers();
  }, []);

  useEffect(() => {
    if (!isEditMode) {
      return;
    }

    const fetchPipelineDetails = async () => {
      setIsLoadingPipeline(true);

      try {
        const response = await api.get(`pipelines/${id}/details/`);
        const pipeline = response.data ?? {};

        setJobName(pipeline.name ?? "");
        setDescription(pipeline.description ?? "");
        setEditorContent(pipeline.main_code ?? "");
        setEditorLanguage("python");
        setCoOwners(
          Array.isArray(pipeline.collaborators)
            ? pipeline.collaborators
                .map((collaborator) => collaborator.username)
                .filter(Boolean)
            : []
        );
      } catch (error) {
        console.error("Erro ao buscar fluxo para edição:", error);
        window.alert("Não foi possível carregar o fluxo para edição.");
      } finally {
        setIsLoadingPipeline(false);
      }
    };

    fetchPipelineDetails();
  }, [id, isEditMode]);

  useEffect(() => {
    if (pendingFocusId === null) {
      return;
    }

    const inputToFocus = libraryInputRefs.current[pendingFocusId];

    if (inputToFocus) {
      inputToFocus.focus();
      setPendingFocusId(null);
    }
  }, [libraries, pendingFocusId]);

  const uploadLabel =
    selectedFiles.length === 0
      ? "Enviar arquivos .py"
      : selectedFiles.length === 1
        ? selectedFiles[0].name
        : `${selectedFiles[0].name} +${selectedFiles.length - 1}`;

  const handleSubmitPipeline = async () => {
    const normalizedLibraries = libraries
      .map((library) => library.value.trim())
      .filter(Boolean);
    const acao = isEditMode ? "salvar" : "criar";

    if (!jobName.trim()) {
      setSubmitModal({
        status: "error",
        message: `Preencha o nome do fluxo antes de ${acao}.`,
        pipelineId: null,
      });
      return;
    }

    if (!editorContent.trim()) {
      setSubmitModal({
        status: "error",
        message: `Adicione ou escreva um script antes de ${acao} o fluxo.`,
        pipelineId: null,
      });
      return;
    }

    setIsSubmitting(true);
    setSubmitModal({
      status: "loading",
      message: isEditMode
        ? "Estamos salvando as alterações do seu fluxo."
        : "Estamos preparando tudo para o seu novo fluxo.",
      pipelineId: null,
    });

    try {
      const formData = new FormData();
      const scriptFile =
        selectedFiles[0] ??
        new File([editorContent], "main.py", {
          type: "text/x-python",
        });

      formData.append("name", jobName.trim());
      formData.append("description", description.trim());
      formData.append("script", scriptFile);

      if (!isEditMode) {
        formData.append("lib", JSON.stringify(normalizedLibraries));
      }

      if (configFile) {
        const fieldName = configFile.name.toLowerCase().endsWith(".ini") ? "config" : "env";
        formData.append(fieldName, configFile);
      }

      const response = isEditMode
        ? await api.put(`pipelines/${id}/update/`, formData, {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          })
        : await api.post("pipelines/create/", formData, {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          });

      const pipelineId = response.data.id ?? id;

      setSubmitModal({
        status: "success",
        message: isEditMode
          ? "Suas alterações foram salvas com sucesso."
          : `"${jobName.trim()}" está pronto para ser executado.`,
        pipelineId,
      });
    } catch (error) {
      console.error(
        isEditMode ? "Erro ao atualizar fluxo:" : "Erro ao criar fluxo:",
        error
      );
      setSubmitModal({
        status: "error",
        message:
          error.response?.data?.error ||
          (isEditMode
            ? "Não foi possível atualizar o fluxo."
            : "Não foi possível criar o fluxo."),
        pipelineId: null,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const closeSubmitModal = () => {
    if (submitModal.status === "loading") return;
    setSubmitModal({ status: "idle", message: "", pipelineId: null });
  };

  const irParaFluxoCriado = () => {
    navigate(`/Details/${submitModal.pipelineId}`);
  };

  if (isLoadingPipeline) {
    return (
      <div className="criar-page">
        <div className="criar-loading">Carregando fluxo...</div>
      </div>
    );
  }

  return (
    <div className="criar-page">
      <div className="criar-shell">
        <header className="criar-header">
          <h1>{isEditMode ? "Editar fluxo" : "Criar novo fluxo"}</h1>
          <p>Configure as informações, o script e as dependências do seu pipeline.</p>
        </header>

        <div className="step-card" data-tour="criar-geral">
          <div className="step-card-header">
            <span className="step-badge">1</span>
            <h3>Configurações gerais</h3>
          </div>
          <div className="step-card-body step-grid">
            <div className="field">
              <label className="field-label" htmlFor="job-name">Nome do fluxo</label>
              <input
                id="job-name"
                className="field-input"
                type="text"
                maxLength="255"
                value={jobName}
                onChange={(event) => setJobName(event.target.value)}
                placeholder="Ex: Carga de vendas diária"
              />
            </div>
            <div className="field">
              <label className="field-label" htmlFor="job-description">Descrição</label>
              <textarea
                id="job-description"
                className="field-input field-textarea"
                maxLength="255"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Descreva o objetivo deste fluxo"
              ></textarea>
            </div>
            <div className="field">
              <label className="field-label" htmlFor="job-owners">Colaboradores</label>
              <div className="owners-input-box">
                {coOwners.map((owner) => (
                  <div key={owner} className="owner-tag">
                    <span>{owner}</span>
                    <button
                      className="owner-tag-remove"
                      onClick={() => removeCoOwner(owner)}
                      type="button"
                      aria-label={`Remover ${owner}`}
                    >
                      ×
                    </button>
                  </div>
                ))}
                <input
                  id="job-owners"
                  list="owners"
                  className="owners-input"
                  type="text"
                  value={inputValue}
                  onChange={(event) => setInputValue(event.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder={
                    coOwners.length === 0
                      ? "Digite ou selecione um colaborador"
                      : ""
                  }
                />
              </div>
              <datalist id="owners">
                {ownersList.map((owner) => (
                  <option key={owner} value={owner} />
                ))}
              </datalist>
            </div>
          </div>
        </div>

        <div className="step-card" data-tour="criar-script">
          <div className="step-card-header">
            <span className="step-badge">2</span>
            <h3>Lógica e script</h3>
          </div>
          <div className="step-card-body script-layout">
            <label
              htmlFor="file-upload"
              className={`upload-box ${dragActive ? "drag-active" : ""}`}
              onDragEnter={(event) => {
                event.preventDefault();
                setDragActive(true);
              }}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <svg className="upload-box-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 7.5A2.5 2.5 0 0 1 6.5 5h3.4a1 1 0 0 1 .8.4l1.2 1.6a1 1 0 0 0 .8.4H17.5A2.5 2.5 0 0 1 20 9.9v6.6a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 16.5v-9Z" />
              </svg>

              <span className="upload-box-button">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 16V4M12 4 8 8M12 4l4 4" />
                  <path d="M4 16v2.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V16" />
                </svg>
                <span className="upload-box-label">{uploadLabel}</span>
              </span>

              <span className="upload-box-hint">Arraste um arquivo .py ou clique para selecionar</span>

              <input
                id="file-upload"
                type="file"
                accept=".py"
                multiple
                onChange={(event) => handleFiles(event.target.files)}
              />
            </label>

            <div className="code-field">
              <Editor
                height="400px"
                defaultLanguage={editorLanguage}
                value={editorContent}
                onChange={syncEditorToSelectedFile}
                options={{
                  selectOnLineNumbers: true,
                  minimap: { enabled: false },
                  fontSize: 14,
                }}
              />
            </div>
          </div>
        </div>

        <div className="step-card" data-tour="criar-config">
          <div className="step-card-header">
            <span className="step-badge">2</span>
            <h3>Arquivo de configuração (.env / config.ini) — opcional</h3>
          </div>
          <div className="step-card-body">
            <p className="step-card-text">
              Você pode fazer upload de um arquivo <strong>.env</strong> ou{" "}
              <strong>config.ini</strong> para fornecer variáveis de ambiente
              ou configurações à sua pipeline.
            </p>
            <label htmlFor="config-upload" className="env-upload-box">
              <input
                id="config-upload"
                type="file"
                accept=".env,.ini"
                onChange={(event) => handleConfigFile(event.target.files)}
                className="env-input"
              />
              <div className="env-upload-label">
                {configFile ? (
                  <>
                    <span className="env-file-name">✓ {configFile.name}</span>
                    <button
                      type="button"
                      className="btn-remove-env"
                      onClick={(e) => {
                        e.preventDefault();
                        setConfigFile(null);
                      }}
                    >
                      Remover
                    </button>
                  </>
                ) : (
                  <span>Clique para selecionar arquivo .env ou config.ini</span>
                )}
              </div>
            </label>
          </div>
        </div>

        <div className="step-card" data-tour="criar-libs">
          <div className="step-card-header">
            <span className="step-badge">3</span>
            <h3>Bibliotecas</h3>
          </div>

          <div className="step-card-body">
            <div className="libs-list">
              {libraries.map((library, index) => (
                <div key={library.id} className="lib-item">
                  <input
                    id={`library-${index}`}
                    className="field-input lib-input"
                    type="text"
                    value={library.value}
                    ref={(element) => {
                      if (element) {
                        libraryInputRefs.current[library.id] = element;
                      } else {
                        delete libraryInputRefs.current[library.id];
                      }
                    }}
                    onChange={(event) => updateLibrary(index, event.target.value)}
                    onKeyDown={(event) => handleLibraryKeyDown(event, index)}
                    placeholder="Digite o nome da biblioteca"
                    readOnly={library.locked}
                  />
                  <button
                    type="button"
                    className="btn-remove-lib"
                    onClick={() => removeLibrary(index)}
                    aria-label={`Remover biblioteca ${library.value || index + 1}`}
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                      <path d="M9 3h6l1 2h4v2H4V5h4l1-2Zm1 6h2v8h-2V9Zm4 0h2v8h-2V9ZM7 9h2v8H7V9Zm-1 11h12l1-13H5l1 13Z" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>

            <div className="criar-submit-row">
              <button
                type="button"
                className="btn-criar-fluxo"
                data-tour="criar-submit"
                onClick={handleSubmitPipeline}
                disabled={isSubmitting}
              >
                {isSubmitting
                  ? isEditMode
                    ? "Salvando..."
                    : "Criando..."
                  : isEditMode
                    ? "Salvar alterações"
                    : "Criar Fluxo"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {submitModal.status !== "idle" && (
        <div
          className="submit-modal-overlay"
          role="presentation"
          onClick={closeSubmitModal}
        >
          <div
            className={`submit-modal ${submitModal.status}`}
            role="dialog"
            aria-modal="true"
            aria-live="polite"
            onClick={(event) => event.stopPropagation()}
          >
            {submitModal.status === "loading" && (
              <span className="submit-modal-icon loading" aria-hidden="true">
                <span className="submit-modal-spinner" />
              </span>
            )}

            {submitModal.status === "success" && (
              <span className="submit-modal-icon success" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m5 13 4 4L19 7" />
                </svg>
              </span>
            )}

            {submitModal.status === "error" && (
              <span className="submit-modal-icon error" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M6 6l12 12M18 6 6 18" />
                </svg>
              </span>
            )}

            <h3 className="submit-modal-title">
              {submitModal.status === "loading" &&
                (isEditMode ? "Salvando alterações..." : "Criando seu fluxo...")}
              {submitModal.status === "success" &&
                (isEditMode ? "Fluxo atualizado!" : "Fluxo criado!")}
              {submitModal.status === "error" && "Ops, algo deu errado"}
            </h3>

            <p className="submit-modal-message">{submitModal.message}</p>

            {submitModal.status === "success" && (
              <div className="submit-modal-actions">
                <button
                  type="button"
                  className="submit-modal-btn primary"
                  onClick={irParaFluxoCriado}
                >
                  Ir para o fluxo
                </button>
                <button
                  type="button"
                  className="submit-modal-btn secondary"
                  onClick={() => navigate("/fluxos")}
                >
                  Ver todos os fluxos
                </button>
              </div>
            )}

            {submitModal.status === "error" && (
              <div className="submit-modal-actions">
                <button
                  type="button"
                  className="submit-modal-btn primary"
                  onClick={closeSubmitModal}
                >
                  Entendi
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default Criar;
