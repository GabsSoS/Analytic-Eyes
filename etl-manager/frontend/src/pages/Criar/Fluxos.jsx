import "./Fluxos.css";
import { useState } from "react";
import FolderIcon from '../../assets/Fluxos/folder .png';
import FolderMiniIcon from '../../assets/Fluxos/mini file.png';

function Criar() {
  const [coOwners, setCoOwners] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);

  const ownersList = ["João", "Maria", "Pedro", "Ana"];

  const addCoOwner = () => {
    if (inputValue.trim() && !coOwners.includes(inputValue.trim())) {
      setCoOwners([...coOwners, inputValue.trim()]);
      setInputValue("");
    }
  };

  const removeCoOwner = (owner) => {
    setCoOwners(coOwners.filter(item => item !== owner));
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addCoOwner();
    }
  };

  const handleFiles = (files) => {
    const pyFiles = Array.from(files || []).filter((file) =>
      file.name.toLowerCase().endsWith(".py")
    );

    setSelectedFiles(pyFiles);
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

  return (
    <div className="container">
      <div className="etapa1">
        <div className="cabecalho">
          <div className="circulo">1</div>
          <h3>CONFIGURAÇÕES GERAIS</h3>
        </div>
        <div className="conteudo">
          <div className="job">
            <p className="paragaf">Nome do Job:</p>
            <input className="inputs-generics" type="text" maxLength="255" />
          </div>
          <div className="Descricao">
            <p className="paragaf">Descrição:</p>
            <textarea className="inputs-desc" maxLength="255"></textarea>
          </div>
          <div className="Co-owners">
            <p className="paragaf">Co-owners:</p>
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
                      ×
                    </button>
                  </div>
                ))}
                <input
                  list="owners"
                  className="inputs-owners"
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={coOwners.length === 0 ? "Digite ou selecione um co-owner" : ""}
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
            <img className="folder-icon" src={FolderIcon} alt="Folder Icon" />

            <div className="upload-button">
              <span className="file-icon">
                <img src={FolderMiniIcon} alt="File Icon" />
              </span>{" "}
              Upload .py Files
            </div>

            <input
              id="file-upload"
              type="file"
              accept=".py"
              multiple
              onChange={(event) => handleFiles(event.target.files)}
            />
          </label>
          {selectedFiles.length > 0 && (
            <div className="selected-files">
              Arquivos prontos: {selectedFiles.map((file) => file.name).join(", ")}
            </div>
          )}
        </div>
        <div className="code-field"></div>
        </div>
        


      </div>
    </div >
  );
}

export default Criar
