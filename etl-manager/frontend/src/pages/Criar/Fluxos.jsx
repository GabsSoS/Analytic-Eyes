import "./Fluxos.css";
import { useEffect, useRef, useState } from "react";
import Editor from "@monaco-editor/react";
import { useNavigate, useParams } from "react-router-dom";
import FolderIcon from "../../assets/Fluxos/folder .png";
import FolderMiniIcon from "../../assets/Fluxos/mini file.png";
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
      window.alert(`Preencha o nome do fluxo antes de ${acao}.`);
      return;
    }

    if (!editorContent.trim()) {
      window.alert(`Adicione ou escreva um script antes de ${acao} o fluxo.`);
      return;
    }

    setIsSubmitting(true);

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

      window.alert(
        isEditMode
          ? "Fluxo atualizado com sucesso!"
          : `Fluxo criado com sucesso! ID: ${pipelineId}`
      );
      navigate(`/Details/${pipelineId}`);
    } catch (error) {
      console.error(
        isEditMode ? "Erro ao atualizar fluxo:" : "Erro ao criar fluxo:",
        error
      );
      window.alert(
        error.response?.data?.error ||
          (isEditMode
            ? "Não foi possível atualizar o fluxo."
            : "Não foi possível criar o fluxo.")
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoadingPipeline) {
    return <div className="container">Carregando fluxo...</div>;
  }

  return (
    <div className="container">
      <div className="etapa1">
        <div className="cabecalho">
          <div className="circulo">1</div>
          <h3>CONFIGURAÇÕES GERAIS</h3>
        </div>
        <div className="conteudo">
          <div className="job">
            <p className="paragaf">Nome do fluxo:</p>
            <input
              className="inputs-generics"
              type="text"
              maxLength="255"
              value={jobName}
              onChange={(event) => setJobName(event.target.value)}
            />
          </div>
          <div className="Descricao">
            <p className="paragaf">Descrição:</p>
            <textarea
              className="inputs-desc"
              maxLength="255"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            ></textarea>
          </div>
          <div className="Co-owners">
            <p className="paragaf">Colaboradores:</p>
            <div className="inputs-owners-wrapper">
              <div className="co-owners-input-box">
                {coOwners.map((owner) => (
                  <div key={owner} className="co-owner-tag">
                    <span>{owner}</span>
                    <button
                      className="btn-remove-owner"
                      onClick={() => removeCoOwner(owner)}
                      type="button"
                    >
                      x
                    </button>
                  </div>
                ))}
                <input
                  list="owners"
                  className="inputs-owners"
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
      </div>

      <div className="etapa2">
          <div className="cabecalho">
          <div className="circulo">2</div>
          <h3>LÓGICA E SCRIPT</h3>
        </div>
        <div className="etp-2">
          <div className="upload-container">
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
              <img className="folder-icon" src={FolderIcon} alt="Ícone de pasta" />

              <div className="upload-button">
                <span className="file-icon">
                  <img src={FolderMiniIcon} alt="Ícone de arquivo" />
                </span>{" "}
                {uploadLabel}
              </div>

              <input
                id="file-upload"
                type="file"
                accept=".py"
                multiple
                onChange={(event) => handleFiles(event.target.files)}
              />
            </label>
          </div>
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

      <div className="etapa3">
        <div className="cabecalho">
          <div className="circulo">2</div>
          <h3>LÓGICA E SCRIPT</h3>
        </div>

        <div className="etapa3-conteudo">
          <h4 className="libs-title">LISTA DE BIBLIOTECAS</h4>

          <div className="libs-lista">
            {libraries.map((library, index) => (
              <div key={library.id} className="lib-item">
                <label className="lib-label" htmlFor={`library-${index}`}>
                  Nome da biblioteca:
                </label>
                <input
                  id={`library-${index}`}
                  className="lib-input"
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
                  placeholder="Digite a biblioteca"
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

          <button
            type="button"
            className="btn-criar-fluxo"
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
  );
}

export default Criar;
